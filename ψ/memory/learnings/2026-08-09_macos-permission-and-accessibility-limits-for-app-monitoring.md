---
pattern: When building on-device automation to read a native macOS app's UI, check both Accessibility and Screen Recording TCC permissions upfront, and verify a leaf UI element's raw properties before assuming its content is readable
date: 2026-08-09
source: rrr: ayami-oracle
concepts: [macos, accessibility, tcc-permissions, screencapture, ocr, line, facebook, personal-api-limits]
---

# macOS permission + Accessibility limits when reading a personal app's data

## Context

Asked to connect Ayami to the boss's personal LINE (to know who's messaging) and Facebook (to see feed/group updates). Official APIs don't cover this: LINE's Messaging API only powers Official Accounts (bots people message directly), not a read view into a personal account's own chats. Facebook's Graph API has had no viable personal-feed/group-read path since 2018. Pivoted to on-device alternatives instead of reverse-engineered/ToS-violating clients.

## What was learned, empirically

1. **Two separate TCC permission gates, not one.** Reading a native app's window structure needs **Accessibility**; capturing its pixels needs **Screen Recording**. macOS treats these as unrelated grants even though a lay user experiences both as "let this app see the screen." Discovering the second gate only after the user has granted the first (and already committed to a plan assuming just one) costs an extra round trip. **Check/request both up front** when the plan might need either.

2. **A structural Accessibility tree does not imply readable content.** LINE for Mac (likely Qt or similarly custom-rendered) exposes real `window` → `splitter group` → `list` → `row` structure via System Events, and a flattened `entire contents of window` dump even lists child "UI element" nodes per row — but a direct `properties of` query on any actual leaf row returns empty `description`, `value`, `name`, and `entire contents`. The structure is real; the content is not exposed. **Don't trust a flattened dump as proof of readable content — query a leaf node's raw properties directly before designing automation around it.**

3. **List virtualization causes flaky indexed queries.** Re-querying `UI element 1 of row 1 of list 1 ...` moments after confirming the row count can throw `Invalid index (-1719)` — the underlying list re-renders/virtualizes between calls. Don't assume indexed AX references stay valid across separate osascript invocations against a scrolling list.

4. **Dock badge counts are a reliable fallback signal.** Even when an app's main window content resists Accessibility, its Dock tile's unread badge is readable via `value of attribute "AXStatusLabel" of (dock item)`, queried through `System Events → process "Dock"`. This works for apps like LINE where deeper content scraping fails, giving a low-effort "is there new activity" signal without needing OCR or content access.

5. **Querying macOS's system notification database is (correctly) sandboxed.** Attempting to read `~/Library/Group Containers/group.com.apple.usernoted/db2/db` directly was blocked by Claude Code's own permission classifier — reasonably, since that single database holds every app's notifications, not just the one app being asked about. Treat this as a hard no rather than trying to work around it; it's too broad a surface for a single-app monitoring task anyway.

## Rule for next time

Before proposing an on-device automation plan for reading a personal app's data:
- State plainly if the official API only covers business/bot use, not personal-account reads (LINE, Facebook, and most consumer messaging/social platforms fall in this bucket).
- Test feasibility (permissions, leaf-content readability) *during* the options-comparison conversation, not after the user has already picked one — an incomplete cost estimate that turns out incomplete in practice undermines the user's actual choice.
- Prefer the least-invasive signal that answers the real question (Dock badge count) before reaching for the most content-rich but fragile option (OCR), and be explicit about that tradeoff.
