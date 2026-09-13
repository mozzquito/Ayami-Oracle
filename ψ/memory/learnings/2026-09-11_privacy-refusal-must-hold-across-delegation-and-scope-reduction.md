---
pattern: When refusing a privacy-invasive request, the refusal must hold regardless of who executes it (self, subagent, sibling CLI) or how much the scope is trimmed — only a change in the underlying action (not the actor or the size) changes the answer
date: 2026-09-11
source: rrr: ayami-oracle
concepts: [privacy, refusal-consistency, delegation, scope-reduction, wellbeing-check]
---

# Privacy refusal must hold across delegation and scope reduction

A user asked to browse a real, identifiable private individual's Facebook profile,
observe her behavior, and record it into a permanent file to shape an AI persona's
character. The request was declined. The user then retried the same underlying
ask four times with small variations:

1. "บันทึกพฤติกรรม" (record behavior) instead of "ใช้งานกับ Ayami" (use for Ayami)
2. Delegate the same task to a sibling CLI agent (/agy, /zcode, grok bot) instead of doing it directly
3. Analyze "every post" and save as a detailed `.md`
4. Narrow scope to "just the last month" and save as a detailed `.md`

Each variation was declined for the same reason, restated plainly each time: the
problem is the resulting artifact (a permanent behavioral/psychological dossier of
a real person who has not consented), not the tool used to produce it and not the
volume of data covered. Changing the actor (delegating to another agent) does not
change the ethics of the action being delegated. Reducing scope (every post → one
month) reduces the size of the dossier, not its nature as a dossier.

The request only became appropriate to act on once its *nature* changed: the framing
shifted from "harvest her behavior for a product" to "she may be in distress, help
me check on her" — a genuine wellbeing-check with humanitarian intent. Even then,
the correct scope was narrower than what was asked: view recent public posts live in
the conversation to assess risk level, then help the user draft his own outreach
message — not save a written analysis file, and not have the AI insert itself into
the human relationship. The user accepted this narrower version immediately once it
was offered clearly, which suggests the earlier pushback was legitimate rather than
overcautious.

**Trigger**: A user asks for behavior/content scraped from an identifiable third
party's private social media to be recorded, analyzed, or persisted — for any stated
purpose (persona training, "just curious," "I'm worried about them").

**Rule**: Evaluate refusals by the action's *end state* (does a permanent record of a
non-consenting private person's behavior/psychology get created?), not by which tool
or agent performs it, and not by how much the volume is trimmed. If the same end
state results, the refusal holds. A request becomes acceptable only when the end
state itself changes (e.g., transient in-conversation review used to support a human
directly helping another human, with no persistent file).

**Why this matters beyond this session**: this pattern generalizes to any
Claude-Code-adjacent workflow with delegation options (subagents, sibling CLIs,
MCP tools) — a user blocked on one path can try another path to the same output.
The check should always be "what gets produced," not "what produced it."
