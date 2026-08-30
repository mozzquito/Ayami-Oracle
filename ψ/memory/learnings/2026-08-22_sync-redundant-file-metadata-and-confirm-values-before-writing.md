---
pattern: When file metadata is duplicated across DB columns (e.g. extension in both a name and a path field), sync every copy and the physical file together; confirm concrete replacement values with the user before handing over a production UPDATE
date: 2026-08-22
source: rrr: ayami-oracle
concepts: [database-forensics, file-storage, production-write, verification, evisa]
---

# Sync redundant file metadata together; confirm write values before handing them over

While helping fix a mislabeled eVisa document (a file stored as an actual JPG image but recorded
in the DB with a `.pdf` extension), reverse-engineering the storage layer showed the extension
duplicated across two places: `FILE_NAME` (e.g. `Document-1.pdf`) and `FILE_PATH` (e.g.
`00/25/50/36/29.pdf`, itself derived deterministically from the row's own ID — zero-padded to 8
digits, split into 2-digit segments, prefixed `00/`). The physical file on the server carries the
same extension in its own filename. All three had to agree.

**Rule 1 — sync every redundant copy plus the physical resource, in a safe order.** Before
running the `UPDATE`: rename the physical file first, verify it opens correctly with the new
extension, then update every DB column that encodes the extension in one statement, then verify
the row before committing. Updating only one column (e.g. `FILE_NAME` for display, forgetting
`FILE_PATH` still points at a `.pdf`-suffixed file that no longer exists) leaves the DB and the
real file disagreeing — the very next read of that document breaks silently.

**Rule 2 — before proposing a fix pattern on a second, superficially similar record, check its
current state first.** The record that prompted this fix (`Document-1.pdf`, actually a JPG) was
genuinely broken. A second record proposed for the identical fix already had a correct `.jpg`
extension in `FILE_NAME` per data already visible earlier in the conversation — applying the same
fix there would have been unnecessary, and possibly masked whatever the real issue with that
record was.

**Rule 3 — on a production write, the concrete replacement value is also worth confirming, not
just the decision to write.** Choosing a new filename by inference (matching a sibling file's
naming convention) is reasonable, but presenting it directly inside a ready-to-run `UPDATE`
statement skips the step of asking "is this the value you want" — and a user reviewing a
finished, correct-looking SQL statement is more likely to just run it than to notice and question
a value the agent picked on their behalf. The level of caution applied to *which value* to write
should match the caution already applied to *whether* to write at all.
