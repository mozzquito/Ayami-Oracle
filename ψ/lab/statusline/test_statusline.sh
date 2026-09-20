#!/bin/bash
# Offline tests for .claude/scripts/statusline-ayami.sh
#   bash ψ/lab/statusline/test_statusline.sh
# Uses a scratch dir under .tmp/, a fake npx on PATH, and STATUSLINE_NO_REFRESH so nothing touches
# the network, the real cache, or the real focus file. Runs the script with /bin/bash (3.2 on macOS).

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
SCRIPT="$ROOT/.claude/scripts/statusline-ayami.sh"
FIX="$HERE/fixtures/live-2.1.278.json"
T="$ROOT/.tmp/statusline-test.$$"
mkdir -p "$T/cache" "$T/bin"
trap 'rm -rf "$T"' EXIT

export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t

pass=0; fail=0
ok()   { pass=$((pass + 1)); }
bad()  { fail=$((fail + 1)); echo "FAIL: $1"; [ -n "$2" ] && printf '      %s\n' "$2"; }
has()  { case "$2" in *"$3"*) ok ;; *) bad "$1 (expected to contain: $3)" "$(printf '%s' "$2" | head -c 400)" ;; esac; }
lacks(){ case "$2" in *"$3"*) bad "$1 (must NOT contain: $3)" "$(printf '%s' "$2" | head -c 400)" ;; *) ok ;; esac; }
eq()   { [ "$2" = "$3" ] && ok || bad "$1" "got [$2] want [$3]"; }
strip() { sed $'s/\033\\[[0-9;]*m//g'; }
ESC=$'\033'
AGO=$(date -v-2H +%Y%m%d%H%M)   # BSD date: 2 h ago = stale, but not yet garbage-collected

# run JSON [VAR=val ...] -> stdout (raw, with colors). Exit code kept in $RC.
run() {
  local json=$1; shift
  printf '%s' "$json" | env STATUSLINE_CACHE_DIR="$T/cache" STATUSLINE_NO_REFRESH=1 \
    STATUSLINE_FOCUS_FILE="$T/focus.md" "$@" /bin/bash "$SCRIPT" 2>"$T/stderr"
  echo $? > "$T/rc"
}
rc() { cat "$T/rc" 2>/dev/null; }
lines() { printf '%s\n' "$1" | wc -l | tr -d ' '; }
fx() { jq -c "$1" "$FIX"; }            # fixture with a jq edit
# runfx 'JQ-EDIT' [VAR=val ...] : run() on the edited fixture. bash 3.2 mangles {a,b} inside quotes nested in "$( )",
# so callers must not write run "$(fx "...{a,b}...")"; this keeps the quoting flat.
runfx() { local j; j=$(jq -c "$1" "$FIX"); shift; run "$j" "$@"; }
rm -f "$T/focus.md"

echo "== fixture (real JSON captured from Claude Code 2.1.278) =="
out=$(run "$(cat "$FIX")"); p=$(printf '%s' "$out" | strip)
eq "fixture exit 0" "$(rc)" 0
has "model + effort" "$p" "🤖 Sonnet 5 (high)"
fxk=$(jq '.context_window.current_usage | ((.input_tokens + .cache_creation_input_tokens + .cache_read_input_tokens) / 1000 | floor)' "$FIX")
has "ctx = input + cache_creation + cache_read (${fxk}k)" "$p" "🧠 ${fxk}k/150k"
lacks "22% limit hidden" "$p" "⚡"
lacks "warm cache -> no cold marker" "$p" "🧊"
lacks "no literal null" "$p" "null"
eq "no stderr noise" "$(cat "$T/stderr")" ""

echo "== context thresholds (same 150k/250k as token-check.sh) =="
for spec in "50000:50k/150k:" "119000:119k/150k:" "130000:130k/150k:33m" "150000:150k/250k:31m" "249000:249k/250k:31m" "260000:260k/250k:31m"; do
  tok=${spec%%:*}; rest=${spec#*:}; want=${rest%%:*}; col=${rest#*:}
  out=$(runfx ".context_window.current_usage={input_tokens:$tok,cache_creation_input_tokens:0,cache_read_input_tokens:0}")
  has "ctx $tok text" "$(printf '%s' "$out" | strip)" "🧠 $want"
  if [ -n "$col" ]; then has "ctx $tok colour $col" "$out" "${ESC}[${col}🧠"; else lacks "ctx $tok uncoloured" "$out" "${ESC}[33m🧠"; fi
done
out=$(runfx ".context_window.current_usage={input_tokens:260000}" | strip)
has "over hard limit -> /forward hint" "$out" "⛔ /forward"
out=$(runfx ".context_window.current_usage={input_tokens:70000}" TOKEN_WARN_K=60 TOKEN_HARD_K=100 | strip)
has "TOKEN_WARN_K/HARD_K honoured" "$out" "🧠 70k/100k"
out=$(runfx ".context_window.current_usage={input_tokens:70000}" TOKEN_WARN_K=abc | strip)
has "bad TOKEN_WARN_K falls back to 150" "$out" "🧠 70k/150k"
out=$(runfx ".context_window.current_usage=null" | strip)
lacks "no usage yet -> no ctx segment" "$out" "🧠"

echo "== rate limits (shown only at >= 60%) =="
soon=$(( $(date +%s) + 7800 ))
out=$(runfx ".rate_limits.five_hour={used_percentage:62.4,resets_at:$soon}" | strip)
has "62% shown, decimals cut" "$out" "⚡5h 62% →"
out=$(runfx ".rate_limits.five_hour={used_percentage:59.9,resets_at:$soon}" | strip)
lacks "59.9% hidden" "$out" "⚡"
out=$(runfx ".rate_limits.five_hour={used_percentage:90,resets_at:$soon}")
has "90% is red" "$out" "${ESC}[31m⚡5h 90%"
out=$(runfx ".rate_limits.seven_day={used_percentage:70,resets_at:\"2999-01-01T00:00:00.123Z\"}" | strip)
has "7d with ISO reset string" "$out" "⚡7d 70% →"
out=$(runfx ".rate_limits.five_hour={used_percentage:75}" | strip)
has "no resets_at -> still shown" "$out" "⚡5h 75%"
lacks "no resets_at -> no arrow" "$out" "→"
out=$(runfx ".rate_limits.five_hour={used_percentage:75,resets_at:1000}" | strip)
lacks "past reset -> no arrow" "$out" "→"
out=$(runfx ".rate_limits={five_hour:\"x\",seven_day:[]}" | strip)
eq "junk rate_limits: exit 0" "$(rc)" 0
lacks "junk rate_limits: hidden" "$out" "⚡"

echo "== malformed / hostile input never breaks it =="
for spec in "empty:" "garbage:not json {" "null:null" "array:[]" "object:{}" "number:42" "string:\"x\"" \
            "effort-string:{\"effort\":\"high\",\"model\":{\"display_name\":\"M\"}}" \
            "model-object:{\"model\":{\"display_name\":{}}}" \
            "usage-string:{\"context_window\":{\"current_usage\":\"lots\"}}" \
            "usage-negative:{\"context_window\":{\"current_usage\":{\"input_tokens\":-5}}}" \
            "cache-junk:{\"prompt_cache\":\"x\"}"; do
  name=${spec%%:*}; body=${spec#*:}
  out=$(run "$body" | strip)
  eq "$name: exit 0" "$(rc)" 0
  [ "$(lines "$out")" -ge 2 ] && ok || bad "$name: at least 2 lines" "$out"
  lacks "$name: no literal null" "$out" "null"
  eq "$name: quiet stderr" "$(cat "$T/stderr")" ""
done
out=$(runfx '.model.display_name="A\u001b[31mB\u0007C"' NO_COLOR=1)
case "$out" in *"$ESC"*) bad "control chars in model name stripped" "$(printf '%s' "$out" | od -c | head -3)" ;; *) ok ;; esac
has "printable rest of the model name survives" "$out" "A[31mBC"

echo "== colours =="
out=$(run "$(cat "$FIX")" NO_COLOR=1)
case "$out" in *"$ESC"*) bad "NO_COLOR -> no escape codes" ;; *) ok ;; esac
out=$(run "$(cat "$FIX")" TERM=dumb)
case "$out" in *"$ESC"*) bad "TERM=dumb -> no escape codes" ;; *) ok ;; esac

echo "== ccusage cache (cost/burn segments only) =="
SID=$(jq -r '.session_id[0:8]' "$FIX")
seed='🤖 Sonnet 5 (high) | 💰 $0.84 session / $32.80 today / $13.56 block (3h 40m left) | 🔥 $10.27/hr ⚠️ (Moderate) | 🧠 102,110 (10%)'
printf '%s\n' "$seed" > "$T/cache/ccusage.$SID.txt"
out=$(run "$(cat "$FIX")" | strip)
has "cost kept" "$out" '💰 $0.84 session / $32.80 today'
has "burn kept" "$out" '🔥 $10.27/hr ⚠️ (Moderate)'
lacks "ccusage's own context dropped (live one wins)" "$out" "102,110"
eq "exactly one 🤖" "$(printf '%s' "$out" | grep -o '🤖' | wc -l | tr -d ' ')" 1
eq "exactly one 🧠" "$(printf '%s' "$out" | grep -o '🧠' | wc -l | tr -d ' ')" 1
printf 'npm WARN deprecated something\n' > "$T/cache/ccusage.$SID.txt"
out=$(run "$(cat "$FIX")" | strip)
lacks "junk cache line never shown" "$out" "npm WARN"
printf '%s\n' "$seed" > "$T/cache/ccusage.$SID.txt"; touch -t "$AGO" "$T/cache/ccusage.$SID.txt"
out=$(run "$(cat "$FIX")" | strip)
has "stale cache is still shown (refresh is async)" "$out" '💰 $0.84'
rm -f "$T/cache/ccusage.$SID.txt"
out=$(run "$(cat "$FIX")" | strip)
lacks "no cache yet -> no cost segment, still renders" "$out" "💰"
has "no cache yet -> model still shown" "$out" "🤖 Sonnet 5"
out=$(runfx '.session_id="../../etc/x"' | strip)
eq "hostile session_id: nothing written outside cache" "$(ls "$T" | tr '\n' ' ')" "bin cache rc stderr "
eq "hostile session_id: exit 0" "$(rc)" 0

echo "== git segment =="
G="$T/repo x ψ"; mkdir -p "$G"
git -C "$G" init -q && git -C "$G" checkout -q -b main && echo a > "$G/f" && git -C "$G" add f && git -C "$G" commit -qm one
gj() { fx ".workspace.current_dir=\"$1\" | .cwd=\"$1\""; }
out=$(run "$(gj "$G")" | strip)
has "clean repo: branch (path with spaces + ψ)" "$out" "🌿 main"
lacks "clean: no counts" "$out" "~1"
echo b >> "$G/f"
out=$(run "$(gj "$G")" | strip); has "modified tracked file -> ~1" "$out" "🌿 main ~1"
git -C "$G" add f
out=$(run "$(gj "$G")" | strip); has "staged -> +1" "$out" "+1"
echo c >> "$G/f"
out=$(run "$(gj "$G")" | strip); has "staged + modified -> +1 ~1" "$out" "+1 ~1"
git -C "$G" commit -qam two
echo new > "$G/untracked"
out=$(run "$(gj "$G")" | strip); lacks "untracked files ignored (slow, noisy)" "$out" "?"
out=$(run "$(gj "$G")")
has "clean branch is green" "$out" "${ESC}[32m🌿 main"
echo b >> "$G/f"
out=$(run "$(gj "$G")"); has "dirty branch is yellow" "$out" "${ESC}[33m🌿 main"
git -C "$G" checkout -q -- f
git -C "$G" checkout -q --detach
out=$(run "$(gj "$G")" | strip); has "detached HEAD -> @sha" "$out" "🌿 @"
eq "detached sha is 7 hex" "$(printf '%s' "$out" | grep -o '@[0-9a-f]\{7\}' | wc -c | tr -d ' ')" 9
git -C "$G" checkout -q main
git -C "$G" worktree add -q "$T/wt" -b side 2>/dev/null
out=$(run "$(gj "$T/wt")" | strip); has "linked worktree marker" "$out" "🌳"
out=$(run "$(gj "$T/not-a-repo")" | strip); lacks "no such dir: no git segment" "$out" "🌿"
eq "no such dir: exit 0" "$(rc)" 0
mkdir -p "$T/plain"; out=$(run "$(gj "$T/plain")" GIT_CEILING_DIRECTORIES="$T" | strip); lacks "plain dir: no git segment" "$out" "🌿"
out=$(runfx ".workspace.git_worktree=\"feat-x\" | .workspace.current_dir=\"$G\" | .cwd=\"$G\"" | strip)
has "worktree name from JSON" "$out" "🌳feat-x"
out=$(runfx ".pr={number:42} | .workspace.current_dir=\"$G\" | .cwd=\"$G\"" | strip); has "PR number" "$out" "🔀#42"
# a submodule also has a .git *file* but is not a linked worktree
git init -q "$T/subsrc" && git -C "$T/subsrc" checkout -q -b main && echo s > "$T/subsrc/f" && git -C "$T/subsrc" add f && git -C "$T/subsrc" commit -qm s
git -C "$G" -c protocol.file.allow=always submodule add -q "$T/subsrc" sub >/dev/null 2>&1
if [ -f "$G/sub/.git" ]; then out=$(run "$(gj "$G/sub")" | strip); has "submodule: branch shown" "$out" "🌿"; lacks "submodule is not a linked worktree" "$out" "🌳"
else bad "test setup: submodule was not created"; fi
# ahead / behind
R="$T/remote.git"; git init -q --bare "$R"; git -C "$G" remote add origin "$R"
git -C "$G" push -q -u origin main 2>/dev/null
echo x >> "$G/f"; git -C "$G" commit -qam ahead
out=$(run "$(gj "$G")" | strip); has "ahead of upstream -> ↑1" "$out" "↑1"
git clone -q -b main "$R" "$T/other" 2>/dev/null; echo y >> "$T/other/f"; git -C "$T/other" commit -qam theirs; git -C "$T/other" push -q origin HEAD:main 2>/dev/null
git -C "$G" fetch -q
out=$(run "$(gj "$G")" | strip); has "behind upstream -> ↓1" "$out" "↓1"; has "and still ahead" "$out" "↑1"
# never take the index lock (would race a user's `git commit`)
: > "$G/.git/index.lock"
out=$(run "$(gj "$G")" | strip); has "index.lock present: still renders branch" "$out" "🌿 main"
rm -f "$G/.git/index.lock"

echo "== line 3: focus =="
out=$(run "$(cat "$FIX")" | strip); eq "no focus file -> exactly 2 lines" "$(lines "$out")" 2
printf 'STATE: working\nTASK: fix the thing\nSINCE: 04:22\n' > "$T/focus.md"
out=$(run "$(cat "$FIX")" | strip); has "working" "$out" "🎯 fix the thing (04:22)"; eq "3 lines" "$(lines "$out")" 3
printf 'STATE: completed\nTASK: done thing\nSINCE: 04:22\n' > "$T/focus.md"
out=$(run "$(cat "$FIX")" | strip); has "completed" "$out" "✅ done thing"; lacks "completed hides since" "$out" "(04:22)"
printf 'STATE: pending\nTASK: waiting\nSINCE: 01:00' > "$T/focus.md"
out=$(run "$(cat "$FIX")" | strip); has "pending + no trailing newline" "$out" "⏸ waiting (01:00)"
printf 'STATE: working\nTASK: old work\nSINCE: 04:22\n' > "$T/focus.md"; touch -t "$(date -v-13H +%Y%m%d%H%M)" "$T/focus.md"
out=$(run "$(cat "$FIX")" | strip); has "focus older than 12 h -> 💤 and no clock time" "$out" "💤 old work"; lacks "stale focus hides SINCE" "$out" "(04:22)"
touch -t "$(date -v-11H +%Y%m%d%H%M)" "$T/focus.md"
out=$(run "$(cat "$FIX")" | strip); has "focus 11 h old is still current" "$out" "🎯 old work (04:22)"
printf 'STATE: working\nTASK: a\x01b\x1b[31mred\nSINCE: 1\n' > "$T/focus.md"
out=$(run "$(cat "$FIX")" NO_COLOR=1); case "$out" in *"$ESC"*) bad "focus control chars stripped" ;; *) ok ;; esac
TH="งานนี้ยาวมากเลยนะ ต้องตัดให้พอดีบรรทัดเพื่อไม่ให้ล้นจอเทอร์มินัลของมอสตอนหลับ ตัดกลางตัวอักษรไม่ได้เด็ดขาด"
printf 'STATE: working\nTASK: %s\nSINCE: 04:22\n' "$TH" > "$T/focus.md"
out=$(run "$(cat "$FIX")" | strip)
printf '%s' "$out" | iconv -f UTF-8 -t UTF-8 >/dev/null 2>&1 && ok || bad "Thai truncation leaves valid UTF-8"
has "Thai task truncated with …" "$out" "…"
long=$(printf '%s\n' "$out" | sed -n 3p)
w100=${#long}
out=$(run "$(cat "$FIX")" COLUMNS=50 | strip); long=$(printf '%s\n' "$out" | sed -n 3p)
[ "${#long}" -lt "$w100" ] && ok || bad "narrow COLUMNS shortens the focus line" "${#long} vs $w100"
printf 'STATE: working\nTASK: \nSINCE: 1\n' > "$T/focus.md"
out=$(run "$(cat "$FIX")" | strip); eq "empty TASK -> no focus line" "$(lines "$out")" 2
rm -f "$T/focus.md"

printf 'STATE: completed \r\nTASK: crlf task\r\nSINCE: 04:22\r\n' > "$T/focus.md"
out=$(run "$(cat "$FIX")" | strip)
has "CRLF + trailing space on STATE still means completed" "$out" "✅ crlf task"; lacks "CRLF: no (since) on completed" "$out" "(04:22)"
case "$out" in *$'\r'*) bad "CRLF: no carriage return leaks into the output" ;; *) ok ;; esac
printf 'STATE: working\nTASK: %s\nSINCE: 04:22\n' "$TH" > "$T/focus.md"
for c in 80x "" -5 "1 2"; do
  out=$(run "$(cat "$FIX")" COLUMNS="$c" | strip); eq "COLUMNS=[$c]: exit 0" "$(rc)" 0; eq "COLUMNS=[$c]: quiet stderr" "$(cat "$T/stderr")" ""
  has "COLUMNS=[$c]: still truncated" "$out" "…"
done
rm -f "$T/focus.md"

echo "== line 3: pending fleet calls (cached count) =="
printf '2 1\n' > "$T/cache/fleet.all.txt"
out=$(run "$(cat "$FIX")" | strip); has "pending with stale" "$out" "⏳2 (1 stale)"
printf '3 0\n' > "$T/cache/fleet.all.txt"
out=$(run "$(cat "$FIX")" | strip); has "pending, none stale" "$out" "⏳3"; lacks "no stale label" "$out" "stale"
for v in "0 0" "x y" "" "-1 0"; do
  printf '%s\n' "$v" > "$T/cache/fleet.all.txt"
  out=$(run "$(cat "$FIX")" | strip); lacks "fleet cache [$v] shows nothing" "$out" "⏳"
done
rm -f "$T/cache/fleet.all.txt"

echo "== cold prompt cache =="
out=$(runfx '.prompt_cache.warm=false | .prompt_cache.recache_tokens_if_cold=145474' | strip)
has "cold cache marker + size" "$out" "🧊 cache cold (~145k to re-cache)"
out=$(runfx '.prompt_cache.warm=false | .prompt_cache.requests=0' | strip); lacks "cold with 0 requests -> hidden" "$out" "🧊"
out=$(runfx 'del(.prompt_cache)' | strip); lacks "no prompt_cache -> hidden" "$out" "🧊"

echo "== refresh path (fake npx: real detach + lock + atomic write + backoff) =="
FAKE_PY="$T/fleet_fake.py"
CNT="$T/npx.count"
# arun [VAR=val ...] : render with refresh ENABLED, fake npx first on PATH, output discarded
arun() { printf '%s' "$(cat "$FIX")" | env PATH="$T/bin:$PATH" STATUSLINE_CACHE_DIR="$T/cache" STATUSLINE_FOCUS_FILE="$T/none" \
           STATUSLINE_FLEET_PY="$FAKE_PY" "$@" /bin/bash "$SCRIPT" >/dev/null 2>&1; }
runs() { [ -f "$CNT" ] && wc -l < "$CNT" | tr -d ' ' || echo 0; }
fresh() { rm -rf "$T/cache" "$CNT"; mkdir -p "$T/cache"; }
cachef="$T/cache/ccusage.$SID.txt"
printf 'import sys\nprint("nothing pending")\n' > "$FAKE_PY"

# 1. slow npx: renders do not wait; parallel renders share one refresh
cat > "$T/bin/npx" <<EOF
#!/bin/bash
echo run >> "$CNT"
cat > /dev/null
sleep 1
printf '🤖 X | 💰 \$9.99 session / \$1 today / \$1 block | 🔥 \$1/hr | 🧠 1 (1%%)\nSECOND LINE MUST NOT APPEAR\n'
EOF
chmod +x "$T/bin/npx"; fresh
t0=$(date +%s); for i in 1 2 3; do arun; done; t1=$(date +%s)
[ $((t1 - t0)) -le 2 ] && ok || bad "3 renders while npx sleeps 1 s must not wait for it" "$((t1 - t0))s"
sleep 3
eq "3 rapid renders -> exactly one npx run (lock)" "$(runs)" 1
eq "cache holds the first line only" "$(cat "$cachef")" '🤖 X | 💰 $9.99 session / $1 today / $1 block | 🔥 $1/hr | 🧠 1 (1%)'
[ -d "$T/cache/ccusage.$SID.lock" ] && bad "lock released after refresh" || ok
out=$(run "$(cat "$FIX")" | strip); has "next render shows the fetched cost" "$out" '💰 $9.99'
fresh; for i in 1 2 3 4 5 6 7 8; do arun & done; wait; sleep 3
eq "8 parallel renders -> exactly one npx run" "$(runs)" 1

# 2. failing npx: previous value survives, and a failure does NOT trigger a retry on every render
printf '#!/bin/bash\necho run >> "%s"\nexit 1\n' "$CNT" > "$T/bin/npx"
printf '%s\n' '🤖 old | 💰 $9.99 kept' > "$cachef"; touch -t "$AGO" "$cachef"; rm -f "$CNT"
arun; sleep 1.5
[ -d "$T/cache/ccusage.$SID.lock" ] && bad "lock released after failed npx" || ok
has "failed npx keeps the previous value" "$(cat "$cachef")" '$9.99 kept'
for i in 1 2 3; do arun; done; sleep 1.5
eq "failed npx: 4 renders inside the TTL -> one attempt, no retry storm" "$(runs)" 1
fresh; rm -f "$CNT"; arun; sleep 1.5; arun; arun; sleep 1.5
eq "no cache + failing npx (offline): one attempt, then an empty marker file" "$(runs)" 1
[ -f "$cachef" ] && [ ! -s "$cachef" ] && ok || bad "empty marker file exists" "$(ls -la "$T/cache" | tail -3)"
out=$(run "$(cat "$FIX")" | strip); lacks "empty marker -> no cost segment, no junk" "$out" "💰"

# 3. hung npx: the whole process group is killed, not just the direct child.
#    The marker is built at run time: a literal in this file would also match any shell whose command line quotes the test source.
MARK="29.$$"
printf '#!/bin/bash\nsleep %s\n' "$MARK" > "$T/bin/npx"; fresh
arun STATUSLINE_CCUSAGE_TIMEOUT=1; sleep 3
[ -d "$T/cache/ccusage.$SID.lock" ] && bad "hung npx: lock released after the time limit" || ok
if pgrep -f "sleep $MARK" >/dev/null; then bad "hung npx: grandchild must be killed with its group" "$(ps -axo pid,pgid,etime,command | grep "[s]leep $MARK" | cut -c1-100)"; pkill -f "sleep $MARK"; else ok; fi

# 4. a lock older than 90 s is dead and gets replaced
printf '#!/bin/bash\necho run >> "%s"\nprintf "🤖 Y | 💰 \\$1 session\\n"\n' "$CNT" > "$T/bin/npx"; fresh
mkdir "$T/cache/ccusage.$SID.lock"; touch -t "$AGO" "$T/cache/ccusage.$SID.lock"
arun; sleep 2
eq "stale lock (>90 s) is replaced and the refresh runs" "$(runs)" 1
printf '#!/bin/bash\necho run >> "%s"\n' "$CNT" > "$T/bin/npx"; fresh; mkdir "$T/cache/ccusage.$SID.lock"
arun; sleep 1
eq "fresh lock (another refresh in flight) -> no second run" "$(runs)" 0
rmdir "$T/cache/ccusage.$SID.lock"

# 5. hostile session id with refresh ENABLED: nothing may be written outside the cache dir
printf '#!/bin/bash\ncat >/dev/null\nprintf "🤖 Z | 💰 \\$2 session\\n"\n' > "$T/bin/npx"; fresh
before=$(find "$T" -not -path "$T/cache*" | sort | md5)
printf '%s' "$(jq -c '.session_id="../../etc/x"' "$FIX")" | env PATH="$T/bin:$PATH" STATUSLINE_CACHE_DIR="$T/cache" STATUSLINE_FOCUS_FILE="$T/none" STATUSLINE_FLEET_PY="$FAKE_PY" /bin/bash "$SCRIPT" >/dev/null 2>&1
sleep 2
after=$(find "$T" -not -path "$T/cache*" | sort | md5)
eq "hostile session_id + refresh: nothing outside the cache dir" "$after" "$before"
[ -f "$T/cache/ccusage.et.txt" ] && ok || bad "hostile session_id: sanitised to [et], refresh wrote ccusage.et.txt inside the cache" "$(ls "$T/cache")"
eq "hostile session_id: only expected file names in the cache" "$(ls "$T/cache" | grep -Evc '^(ccusage\.et\.(in|txt)|fleet\.all\.txt)$')" 0

# 6. fleet refresh (fake fleet.py): parsing of the real `pending` output shape
fleet_case() {   # NAME EXPECTED_CACHE  (fake fleet.py body comes from stdin)
  fresh; printf '#!/bin/bash\n' > "$T/bin/npx"; chmod +x "$T/bin/npx"; cat > "$FAKE_PY"
  arun; sleep 2
  eq "fleet refresh: $1" "$(cat "$T/cache/fleet.all.txt" 2>/dev/null | tr -d '\n')" "$2"
}
fleet_case "nothing pending -> 0 0" "0 0" <<'PY'
print("nothing pending")
PY
fleet_case "header + 2 rows, 1 STALE -> 2 1" "2 1" <<'PY'
print("ID        AGENT     AGE     LABEL")
print("11111111  zcode     5m      review one")
print("22222222  agy       20h     STALE  review two")
PY
fleet_case "header only line mentioning STALE is not counted" "1 0" <<'PY'
print("ID        AGENT     AGE     LABEL  (STALE marks old ones)")
print("11111111  zcode     5m      review one")
PY
fleet_case "fleet.py crashes -> empty marker (retry after TTL, no storm)" "" <<'PY'
import sys; sys.exit(3)
PY
out=$(run "$(cat "$FIX")" STATUSLINE_FLEET_PY="$FAKE_PY" | strip); lacks "crashed fleet.py shows nothing" "$out" "⏳"
rm -f "$FAKE_PY"; printf '#!/bin/bash\n' > "$T/bin/npx"

echo "== environment =="
out=$(printf '%s' "$(cat "$FIX")" | env PATH=/usr/bin:/bin STATUSLINE_CACHE_DIR="$T/cache" STATUSLINE_NO_REFRESH=1 /bin/bash "$SCRIPT" 2>&1); rc=$?
eq "no jq on PATH: exit 0" "$rc" 0; has "no jq on PATH: minimal line" "$out" "📁"
out=$(run "$(cat "$FIX")" LC_ALL=C LANG=C | strip); has "runs under a hostile LC_ALL" "$out" "🤖 Sonnet 5"
out=$(printf '%s' "$(cat "$FIX")" | env -i HOME="$HOME" STATUSLINE_CACHE_DIR="$T/cache" STATUSLINE_NO_REFRESH=1 /bin/bash "$SCRIPT" 2>&1); rc=$?
eq "empty environment (no PATH): exit 0" "$rc" 0
n=0; s0=$(date +%s%N 2>/dev/null); [ "${#s0}" -lt 15 ] && s0=$(python3 -c 'import time;print(int(time.time()*1e9))')
for i in 1 2 3 4 5; do run "$(cat "$FIX")" >/dev/null; done
s1=$(python3 -c 'import time;print(int(time.time()*1e9))'); avg=$(( (s1 - s0) / 5000000 ))
echo "   (average render on cache hit: ${avg} ms)"
[ "$avg" -lt 400 ] && ok || bad "render under 400 ms on cache hit" "${avg} ms"

echo
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
