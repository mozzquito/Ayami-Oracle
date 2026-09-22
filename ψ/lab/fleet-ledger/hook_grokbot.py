#!/usr/bin/env python3
"""PreToolUse hook for mcp__grokbot__grokbot_send: record the send in the fleet ledger (see DESIGN.md, "Grok Bot auto-log").

Reads the hook JSON on stdin, hands only the prompt HASH to fleet (prompt goes to fleet through a pipe, never into a shell
or an argv), label is a fixed string (rule M3: no prompt text in the ledger). ALWAYS exits 0 and prints nothing on stdout:
it must never block or alter the send. A denied or failed send can leave a pending `sent`; `fleet abandon` clears it.
"""
import json
import subprocess
import sys
from pathlib import Path

FLEET = Path(__file__).with_name("fleet.py")
TOOL = "mcp__grokbot__grokbot_send"
LABEL = "grokbot send (auto-logged)"


def run() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except ValueError:
        return
    if not isinstance(data, dict) or data.get("tool_name") != TOOL:
        if "grokbot" in raw:  # do not let a wrong assumption about the payload shape turn this into a silent no-op
            print("fleet-hook: grokbot-looking payload with an unexpected tool_name/shape, nothing logged", file=sys.stderr)
        return
    tool_input = data.get("tool_input")
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    message_id, prompt = tool_input.get("messageId"), tool_input.get("prompt")
    if not isinstance(message_id, str) or not isinstance(prompt, str):
        print("fleet-hook: no messageId/prompt in tool_input, nothing logged", file=sys.stderr)
        return
    r = subprocess.run([sys.executable, str(FLEET), "log", "sent", "--agent", "grokbot", "--id", message_id,
                        "--label", LABEL, "--prompt-file", "-"],
                       input=prompt.encode("utf-8"), capture_output=True, timeout=15)
    if r.returncode != 0:  # e.g. duplicate id when the same messageId is re-sent to inspect a submission
        print("fleet-hook: not logged: " + r.stderr.decode("utf-8", errors="replace").strip()[:200], file=sys.stderr)


def main() -> int:
    try:
        run()
    except BaseException as e:  # fail-open on anything, Ctrl-C included
        print(f"fleet-hook: {type(e).__name__}: {str(e)[:100]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
