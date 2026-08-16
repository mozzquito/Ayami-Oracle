---
pattern: When documenting a service manager's crash-restart behavior (launchd KeepAlive, systemd Restart=, Docker restart policies), verify it with an actual kill test before writing it down as fact — don't let "the docs say so" substitute for "I checked this configuration."
date: 2026-08-09
source: rrr: ayami-oracle
concepts: [launchd, verify-before-assert, service-persistence, process-supervision]
---

# Verify service-manager restart claims empirically, not just from memory

Recalling the correct semantics of a config key (e.g. `KeepAlive.SuccessfulExit=false` means
"restart only on non-zero exit, not on clean exit") from documentation or training is not the
same as confirming a *specific* configuration actually behaves that way. The gap between
"this is what the docs say" and "I ran a test and watched it happen" is exactly where subtle
misconfigurations (wrong boolean polarity, an interacting key like `ThrottleInterval`, an
`Only`/`Networking` gate not set as expected) hide until the user finds out the hard way —
often at the worst possible time, since the whole point of the config was unattended recovery.

**Concrete case**: set up a `launchd` user agent for a Discord bot with
`KeepAlive.SuccessfulExit=false`, documented it in the project README as "auto-restarts only
on crash," and initially left it there as an asserted-but-untested claim. Caught this while
writing a retrospective's AI Diary section (the act of narrating the decision surfaced the
gap) and closed it immediately: `kill -9`'d the managed process, confirmed `launchd` respawned
it within the expected `ThrottleInterval`, and the bot came back online. Five seconds of work
to convert an assumption into a verified fact.

**How to apply**: Before writing a claim about *behavior under failure* (restart-on-crash,
retry-on-timeout, failover-on-disconnect) into documentation or a reply to a user, ask: did I
run something that actually exercises this path, or am I recalling/reasoning about what
*should* happen? If the check is cheap (a kill, a forced timeout, a disconnect), just run it —
the cost of verifying is almost always smaller than the cost of the user discovering the gap
during a real incident.

**Project-specific note**: this is the third `/rrr` in the `ayami-oracle` project to flag some
shape of "asserted before verifying" (see [[2026-08-09_check-visible-context-before-asking]]
for the second occurrence, same session). Per the project's own session-metrics rule, three
occurrences of the same friction/error theme means the next step is a root-cause fix (a stated
default habit) rather than another individually-logged instance.
