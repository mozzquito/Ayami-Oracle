---
pattern: "Before starting a network-facing service with a security-relevant default (anonymous auth, non-localhost bind), ask first — don't disclose after"
date: 2026-08-15
source: "rrr: ayami-oracle"
concepts: [security, consent, network-services, mqtt, disclose-vs-ask]
---

# Ask before security-relevant service defaults, not after

While installing `claude-browser-proxy` (a Soul-Brews-Studio tool bridging Claude Code
and the browser via MQTT), the upstream README's own setup steps call for a Mosquitto
broker with `allow_anonymous true` and a websocket listener with no bind address —
meaning any device on the local network can talk to the broker with zero auth. I ran
`brew services start mosquitto` with that config and only flagged the tradeoff *after*
the service was already running, in the same message as reporting completion.

## What happened

The task was "install claude-browser-proxy" — a reasonable, low-drama request. But one
of its dependencies (Mosquitto configured per the upstream docs) opens a genuinely
exposed listener. I treated "the upstream project's own README recommends this" as
license to just do it, the same way I'd treat `npm install` — but a network service
with anonymous access on a shared interface is a different risk class than installing
a package. Disclosure after the fact ("⚠️ note: this opens...") is not the same as
consent before the fact.

## The fix

When a sub-step of an approved task introduces a new risk category not implied by the
original request — specifically: opening a network listener, weakening auth, exposing
a port beyond localhost — stop and ask before executing that specific sub-step, even
if the overall task was already approved. "The user approved installing X" does not
transitively approve every security-relevant default X's setup docs recommend. This
is the same standard already applied correctly elsewhere in the same session (paused
and asked before touching `maw-codex-team-kit`'s runtime conflict rather than guessing)
— just missed here because MQTT setup felt like "just following the README" rather than
an architecture decision.
