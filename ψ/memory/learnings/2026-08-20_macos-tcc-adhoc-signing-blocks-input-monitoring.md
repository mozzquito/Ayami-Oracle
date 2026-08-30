---
pattern: ad-hoc code signing silently blocks macOS Input Monitoring/Accessibility TCC prompts — debug live with `log stream --predicate 'process == "tccd"'`, not app-side API return values alone
date: 2026-08-20
source: rrr: ayami-oracle
concepts: [macos, tcc, codesign, input-monitoring, accessibility, privacy-permissions, debugging]
---

# macOS ad-hoc signing blocks Input Monitoring/Accessibility TCC prompts — debug via tccd log, not app-side checks

Building a menu-bar app (`ψ/lab/quack-keyboard`) that needs `NSEvent.addGlobalMonitorForEvents(matching: .keyDown)` — this requires the user to grant Input Monitoring permission. On modern macOS (confirmed on a 26.x build), the app never got the chance: `tccd` silently refused to show the consent dialog at all, with no error surfaced to the app beyond a boolean `false`.

## What actually happened (two distinct failure modes)

1. **Ad-hoc signature (`codesign --sign -`) has no embedded code requirement.** `codesign -dvvv` showed `flags=0x2(adhoc)` and `Internal requirements count=0`. `tccd`'s own log (captured live) showed: `Failed to match existing code requirement for subject <bundle-id> and service kTCCServiceAccessibility` — it couldn't verify the app's identity, so it defaulted to deny without prompting.

2. **Even after fixing #1 with a real (self-signed) certificate** — `openssl req -x509 ...` + `security import` + `security add-trusted-cert -p codeSign` — the code-requirement match succeeded (`Internal requirements count=1`, `Authority=<cert CN>`), but `tccd` still refused: `Service kTCCServiceListenEvent does not allow prompting; returning denied.` This points to a stricter policy: only identities that chain back to Apple's own CA (a free "Apple Development" cert via Xcode+Apple ID, or a paid Developer ID) are eligible for `tccd` to ever show the interactive alert. A fully self-signed cert, even a structurally valid one, doesn't qualify.

Neither failure mode produced an error the app itself could see beyond `IOHIDCheckAccess`/`IOHIDRequestAccess` returning "denied" — no exception, no distinguishing signal between "user hasn't decided yet" and "system will never ask."

## The fix that mattered

Don't debug this from the app side. Run, live, while the app makes its request:

```bash
log stream --predicate 'process == "tccd"' --style compact
```

This surfaces the actual internal reasoning (`Failed to match existing code requirement`, `does not allow prompting; returning denied`, etc.) that the app-facing APIs never expose. `tccutil reset <Service> <bundle-id>` clears a denied/unknown state between test iterations so each `open` gives a clean read.

## Rule for next time

Before writing any Input Monitoring / Accessibility / Screen Recording permission-request code on macOS, check the build's signing identity FIRST with `codesign -dvvv <bundle>` — if it shows `flags=0x2(adhoc)` or `Internal requirements count=0`, fix signing before writing a single line of permission-handling logic; that's the actual blocker, not application logic. If a proper (Apple-chained) signing identity isn't available yet, expect these permissions not to work at all — no amount of app-side retry/request logic will make `tccd` prompt for an ad-hoc or purely self-signed binary.

See [[2026-08-20_quack-keyboard-tcc-debugging]] retrospective for the full session trace.
