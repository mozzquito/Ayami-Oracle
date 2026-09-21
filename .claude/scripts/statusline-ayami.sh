#!/bin/bash
# statusline-ayami.sh — Claude Code statusLine for this repo (2026-09-21).
#
# stdin : JSON from Claude Code (https://code.claude.com/docs/en/statusline)
# stdout: 2-3 lines. Never fails, never blocks: every piece degrades to empty.
#
# Line 1  🤖 model (effort) | 💰🔥 cost + burn (ccusage, cached) | ⚡ 5h/7d limit (>=60%) | 🧠 ctx vs 150k/250k
# Line 2  📁 dir on 🌿 branch +staged ~modified ↑ahead ↓behind 🌳 🔀PR • 📡 session • HH:MM
# Line 3  🎯 focus (ψ/inbox/focus-agent-<AGENT_ID>.md) • ⏳ pending fleet calls   (omitted when empty)
#
# Design, tests, rollback: ψ/lab/statusline/README.md
# Env: NO_COLOR; TOKEN_WARN_K (150) / TOKEN_HARD_K (250) = same knobs as token-check.sh;
#      STATUSLINE_DEBUG=1 (or touch <cache>/debug) dumps the last stdin to <cache>/last.json;
#      STATUSLINE_CACHE_DIR, STATUSLINE_FOCUS_FILE, STATUSLINE_NO_REFRESH=1 (tests).
# Must run on macOS bash 3.2: no $EPOCHSECONDS, no associative arrays, no ${x,,}. No `set -e`.

export LC_ALL=en_US.UTF-8 GIT_OPTIONAL_LOCKS=0
umask 077

SELF="$(cd "$(dirname "$0")" 2>/dev/null && pwd)/$(basename "$0")"
ROOT="$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd)"
[ -n "$ROOT" ] || ROOT="$PWD"
CACHE="${STATUSLINE_CACHE_DIR:-$ROOT/.tmp/statusline}"
FLEET_PY="${STATUSLINE_FLEET_PY:-$ROOT/ψ/lab/fleet-ledger/fleet.py}"
CCUSAGE_SPEC="${STATUSLINE_CCUSAGE_SPEC:-ccusage@latest}"   # pin here (e.g. ccusage@1.2.3) to stop running whatever npm serves
US=$'\037'
mkdir -p "$CACHE" 2>/dev/null

now() { date +%s; }
mtime() { stat -f %m "$1" 2>/dev/null || echo 0; }   # BSD stat; a missing file reads as "very old"
isnum() { case "$1" in ''|*[!0-9]*) return 1 ;; esac; return 0; }
# capped SECONDS CMD... : hard time limit without GNU timeout (perl ships with macOS).
# The command runs in its own process group and the whole group is killed on timeout: killing only the
# direct child (plain alarm+exec) leaves grandchildren such as node holding our pipe open.
capped() {
  local s=$1; shift
  if command -v perl >/dev/null 2>&1; then
    perl -e 'my $t = shift; my $pid = fork(); defined $pid or exec @ARGV;
             if (!$pid) { setpgrp(0, 0); exec @ARGV; exit 127 }
             $SIG{ALRM} = sub { kill "KILL", -$pid; kill "KILL", $pid };
             alarm $t; my $r = waitpid($pid, 0); waitpid($pid, 0) if $r < 0; exit($? >> 8)' "$s" "$@"
  else
    "$@"
  fi
}

# ---------------------------------------------------------------- refresh mode
# Re-invoked detached by kick(): fetch one slow value, write it atomically, drop the lock.
if [ "$1" = "--refresh" ]; then
  kind=$2; key=$3
  f="$CACHE/$kind.$key.txt"; lock="$CACHE/$kind.$key.lock"; tmp="$f.tmp.$$"
  trap 'rmdir "$lock" 2>/dev/null; rm -f "$tmp"' EXIT
  out=""
  case "$kind" in
    ccusage)
      # -y: never stop on an install prompt. First line only, so npx/npm chatter cannot leak in.
      out=$(capped "${STATUSLINE_CCUSAGE_TIMEOUT:-25}" npx -y "$CCUSAGE_SPEC" statusline --visual-burn-rate emoji-text < "$CACHE/ccusage.$key.in" 2>/dev/null | head -n 1)
      [ ${#out} -le 1000 ] || out="" ;;
    fleet)
      p=$(capped 5 python3 "$FLEET_PY" pending 2>/dev/null)
      if [ -n "$p" ]; then
        case "$p" in
          "nothing pending"*) out="0 0" ;;
          *) n=$(printf '%s\n' "$p" | tail -n +2 | grep -c .); st=$(printf '%s\n' "$p" | tail -n +2 | grep -c ' STALE '); out="$n $st" ;;
        esac
      fi ;;
  esac
  if [ -n "$out" ]; then
    printf '%s\n' "$out" > "$tmp" && mv -f -- "$tmp" "$f"
  elif [ -f "$f" ]; then
    touch "$f"        # failed: keep the last good value and retry only after the TTL
  else
    : > "$f"          # nothing yet: an empty file still rate-limits retries (offline, broken npx)
  fi
  exit 0
fi

# kick KIND KEY : start ONE detached refresh (mkdir lock; a lock older than 90 s is stale)
kick() {
  [ -n "$STATUSLINE_NO_REFRESH" ] && return 0
  local lock="$CACHE/$1.$2.lock"
  if [ -d "$lock" ] && [ $(( $(now) - $(mtime "$lock") )) -gt 90 ]; then rmdir "$lock" 2>/dev/null; fi
  mkdir "$lock" 2>/dev/null || return 0
  find "$CACHE" -type f -mtime +1 -delete 2>/dev/null
  [ "$1" = ccusage ] && printf '%s' "$input" > "$CACHE/ccusage.$2.in"
  if command -v perl >/dev/null 2>&1; then
    # new session: survives if Claude Code kills this script's process group on the next refresh
    perl -MPOSIX -e 'POSIX::setsid(); exec @ARGV' bash "$SELF" --refresh "$1" "$2" </dev/null >/dev/null 2>&1 &
  else
    bash "$SELF" --refresh "$1" "$2" </dev/null >/dev/null 2>&1 &
  fi
}
# cached KIND KEY TTL [IDLE] : print the cached value (maybe stale, maybe nothing) and refresh when older than TTL.
# IDLE non-empty = a refreshInterval tick with nothing new: a missing cache is still created, an existing one is left alone.
cached() {
  local f="$CACHE/$1.$2.txt"
  if [ ! -f "$f" ]; then kick "$1" "$2"
  elif [ -z "$4" ] && [ $(( $(now) - $(mtime "$f") )) -ge "$3" ]; then kick "$1" "$2"; fi
  [ -f "$f" ] && cat "$f"
}

# --------------------------------------------------------------------- render
input=$(cat)

if [ -n "$STATUSLINE_DEBUG" ] || [ -f "$CACHE/debug" ]; then printf '%s' "$input" > "$CACHE/last.json"; fi

if ! command -v jq >/dev/null 2>&1; then
  echo "📁 ${PWD/#$HOME/~} • $(date +%H:%M)"; exit 0
fi

JQ='
def s: (if . == null then "" else tostring end) | explode | map(select(. >= 32 and . != 127)) | implode;
def g(f): try (f | s) catch "";
def ts(f): try (f | if type == "number" then ((if . > 100000000000 then ./1000 else . end) | floor | tostring)
                    elif type == "string" then (sub("\\.[0-9]+"; "") | fromdateiso8601 | tostring)
                    else "" end) catch "";
[ g(.model.display_name // .model.id),
  g(.effort.level),
  g(.fast_mode),
  g(.workspace.current_dir // .cwd),
  (g(.session_id) | .[0:8]),
  (try ((.context_window.current_usage // {}) | ((.input_tokens // 0) + (.cache_creation_input_tokens // 0) + (.cache_read_input_tokens // 0)) | floor | tostring) catch ""),
  g(.rate_limits.five_hour.used_percentage), ts(.rate_limits.five_hour.resets_at),
  g(.rate_limits.seven_day.used_percentage), ts(.rate_limits.seven_day.resets_at),
  g(.workspace.git_worktree // .worktree.name),
  g(.pr.number),
  g(.prompt_cache.warm), g(.prompt_cache.requests),
  (try (.prompt_cache.recache_tokens_if_cold | floor | tostring) catch ""),
  ts(.prompt_cache.expires_at),
  g(.cost.total_api_duration_ms)
] | join("\u001f")'
IFS="$US" read -r model effort fast cwd sid used rl5 rl5_at rl7 rl7_at wt pr pcw pcr pct pce api \
  <<< "$(printf '%s' "$input" | jq -r "$JQ" 2>/dev/null)"
sid=${sid//[^A-Za-z0-9-]/}
# idle tick (a refreshInterval re-render with no new API activity since the last render): spend cannot have changed,
# so do not re-run ccusage. A missing cache is still created; anything unreadable counts as "not idle" (= refresh as before).
idle=""
if [ -n "$sid" ] && isnum "${api%%.*}"; then
  if [ "$(cat "$CACHE/lastapi.$sid" 2>/dev/null)" = "$api" ]; then idle=1; else printf '%s\n' "$api" > "$CACHE/lastapi.$sid" 2>/dev/null; fi
fi
[ -n "$cwd" ] || cwd="$PWD"

if [ -n "$NO_COLOR" ] || [ "$TERM" = dumb ]; then
  R=""; D=""; G=""; Y=""; RD=""
else
  R=$'\033[0m'; D=$'\033[2m'; G=$'\033[32m'; Y=$'\033[33m'; RD=$'\033[31m'
fi

# ---- line 1: model | cost | limits | context
[ -n "$model" ] || model="?"
l1="🤖 $model"
case "$model" in *"("*) ;; *) [ -n "$effort" ] && l1="$l1 ($effort)" ;; esac
[ "$fast" = true ] && l1="$l1 ⚡fast"

if [ -n "$sid" ]; then
  cc=$(cached ccusage "$sid" 30 "$idle")
  if [ -n "$cc" ]; then
    # keep ccusage's cost/burn segments only: model and context are rendered live from stdin
    cc_mid=""; set -f; oIFS=$IFS; IFS='|'
    for seg in $cc; do
      seg="${seg# }"; seg="${seg% }"
      case "$seg" in 💰*|🔥*) cc_mid="${cc_mid:+$cc_mid | }$seg" ;; esac
    done
    IFS=$oIFS; set +f
    [ -n "$cc_mid" ] && l1="$l1 | $cc_mid"
  fi
fi

limit_seg() {   # LABEL PCT RESET_EPOCH FORMAT : only when >= 60%
  local p=${2%%.*}
  isnum "$p" && [ "$p" -ge 60 ] || return 0
  local c=$Y at=""
  [ "$p" -ge 85 ] && c=$RD
  if isnum "$3" && [ "$3" -gt "$(now)" ]; then at=" →$(date -r "$3" "+$4" 2>/dev/null)"; fi
  printf '%s' "${c}⚡$1 ${p}%${at}${R}"
}
rl=$(limit_seg 5h "$rl5" "$rl5_at" %H:%M)
[ -n "$rl" ] && l1="$l1 | $rl"
rl=$(limit_seg 7d "$rl7" "$rl7_at" %a)
[ -n "$rl" ] && l1="$l1 | $rl"

if isnum "$used" && [ "$used" -gt 0 ]; then
  uk=$(( used / 1000 )); warn=${TOKEN_WARN_K:-150}; hard=${TOKEN_HARD_K:-250}
  isnum "$warn" || warn=150; isnum "$hard" || hard=250
  if   [ "$uk" -ge "$hard" ]; then c=$RD; lim=$hard; mark=" ⛔ /forward"
  elif [ "$uk" -ge "$warn" ]; then c=$RD; lim=$hard; mark=""
  elif [ $(( uk * 5 )) -ge $(( warn * 4 )) ]; then c=$Y; lim=$warn; mark=""
  else c=""; lim=$warn; mark=""; fi
  l1="$l1 | ${c}🧠 ${uk}k/${lim}k${mark}${R}"
fi

# ---- line 2: dir, git, session, time
git_seg=""
gs=$(capped 2 git -C "$cwd" status --porcelain=v2 --branch --untracked-files=no 2>/dev/null | awk '
  /^# branch.oid/  { oid = $3 }
  /^# branch.head/ { h = $3 }
  /^# branch.ab/   { a = substr($3, 2); b = substr($4, 2) }
  /^[12u] /        { x = substr($2, 1, 1); y = substr($2, 2, 1); if (x != ".") s++; if (y != ".") m++ }
  END { if (h != "") printf "%s\037%s\037%d\037%d\037%d\037%d\n", h, oid, a, b, s, m }')
if [ -n "$gs" ]; then
  IFS="$US" read -r gh goid ga gb gsg gm <<< "$gs"
  [ "$gh" = "(detached)" ] && gh="@${goid:0:7}"
  c=$G; { [ "${gsg:-0}" -gt 0 ] || [ "${gm:-0}" -gt 0 ]; } 2>/dev/null && c=$Y
  git_seg=" on ${c}🌿 ${gh}${R}"
  [ "${gsg:-0}" -gt 0 ] 2>/dev/null && git_seg="$git_seg +${gsg}"
  [ "${gm:-0}" -gt 0 ]  2>/dev/null && git_seg="$git_seg ~${gm}"
  [ "${ga:-0}" -gt 0 ]  2>/dev/null && git_seg="$git_seg ↑${ga}"
  [ "${gb:-0}" -gt 0 ]  2>/dev/null && git_seg="$git_seg ${Y}↓${gb}${R}"
  if [ -z "$wt" ] && [ -f "$cwd/.git" ]; then
    case "$(git -C "$cwd" rev-parse --git-dir 2>/dev/null)" in */worktrees/*) wt="linked" ;; esac
  fi
  [ -n "$wt" ] && git_seg="$git_seg 🌳${wt}"
  [ -n "$pr" ] && git_seg="$git_seg 🔀#${pr}"
fi
l2="📁 ${cwd/#$HOME/~}${git_seg}"
[ -n "$sid" ] && l2="$l2 • 📡 ${D}${sid}${R}"
l2="$l2 • $(date +%H:%M)"

# ---- line 3 (only when there is something): focus, pending agent calls
l3=""
agent=${AGENT_ID:-main}; agent=${agent//[^A-Za-z0-9_-]/}; [ -n "$agent" ] || agent=main
FOCUS="${STATUSLINE_FOCUS_FILE:-$ROOT/ψ/inbox/focus-agent-$agent.md}"
if [ -f "$FOCUS" ]; then
  st=""; task=""; since=""
  while IFS= read -r ln || [ -n "$ln" ]; do
    case "$ln" in STATE:*) st="${ln#STATE:}" ;; TASK:*) task="${ln#TASK:}" ;; SINCE:*) since="${ln#SINCE:}" ;; esac
  done < "$FOCUS"
  st="${st//[[:space:]]/}"; task="${task# }"
  since="${since%$'\r'}"; since="${since# }"; since="${since% }"
  task=$(printf '%s' "$task" | tr -d '\000-\037\177')
  cols=${COLUMNS:-100}; isnum "$cols" || cols=100
  max=$(( cols - 24 )); [ "$max" -lt 24 ] && max=24; [ "$max" -gt 90 ] && max=90
  [ ${#task} -gt "$max" ] && task="${task:0:$((max - 1))}…"
  if [ -n "$task" ]; then
    case "$st" in
      completed) ic="✅"; c=$D ;;
      pending)   ic="⏸";  c=$Y ;;
      jumped)    ic="↪";  c=$D ;;
      *)         ic="🎯"; c=""  ;;
    esac
    # a focus file untouched for 12 h is yesterday's news: dim it and say so instead of posing as current
    if [ $(( $(now) - $(mtime "$FOCUS") )) -gt 43200 ]; then ic="💤"; c=$D; st="stale"; fi
    l3="${c}${ic} ${task}${R}"
    [ -n "$since" ] && [ "$st" != completed ] && [ "$st" != stale ] && l3="$l3 ${D}(${since})${R}"
  fi
fi
# prompt cache. Cold (or warm but already past expires_at): the next message re-writes the whole context at full price.
# Warm but close to expiry: a minute countdown, so the user can act before it goes cold. Hidden while comfortably warm.
if isnum "$pcr" && [ "$pcr" -gt 0 ]; then
  left=""; isnum "$pce" && left=$(( pce - $(now) ))
  if [ "$pcw" = false ] || { [ "$pcw" = true ] && [ -n "$left" ] && [ "$left" -le 0 ]; }; then
    cold="🧊 cache cold"
    isnum "$pct" && [ "$pct" -gt 0 ] && cold="$cold (~$(( pct / 1000 ))k to re-cache)"
    l3="${l3:+$l3 • }${Y}${cold}${R}"
  elif [ "$pcw" = true ] && [ -n "$left" ]; then
    m=$(( (left + 59) / 60 )); show=${STATUSLINE_CACHE_SHOW_MIN:-30}; isnum "$show" || show=30
    if [ "$m" -le "$show" ]; then
      c=$D; [ "$m" -le 10 ] && c=$Y
      if [ "$m" -ge 60 ]; then cdown="$(( m / 60 ))h$(printf %02d $(( m % 60 )))m"; else cdown="${m}m"; fi
      l3="${l3:+$l3 • }${c}🧊 ${cdown}${R}"
    fi
  fi
fi
if [ -f "$FLEET_PY" ]; then
  read -r pn ps <<< "$(cached fleet all 60)"
  if isnum "$pn" && [ "$pn" -gt 0 ]; then
    c=$Y; seg="⏳${pn}"
    if isnum "$ps" && [ "$ps" -gt 0 ]; then c=$RD; seg="$seg (${ps} stale)"; fi
    l3="${l3:+$l3 • }${c}${seg}${R}"
  fi
fi

printf '%s\n' "$l1"
printf '%s\n' "$l2"
[ -n "$l3" ] && printf '%s\n' "$l3"
exit 0
