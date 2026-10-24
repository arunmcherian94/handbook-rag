#!/usr/bin/env python3
"""PreToolUse hook on Bash (spec 0009, AC-2): a command that may spend needs a human click, in
every permission mode. Anything else passes silently.

Matched broadly on purpose: any CONFIRM assignment (quoted or not, any value) and any `--conf`
prefix (argparse accepts abbreviations of --confirm). A false prompt costs a click; a miss costs
money. A payload the hook can't read also asks: the guard never fails open.
"""

import json
import re
import sys

PAID = re.compile(r"\bCONFIRM\b|--conf")
ASK = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": "may spend (CONFIRM / --confirm): needs Arun's approval",
    }
}


def main() -> int:
    try:
        command = json.load(sys.stdin)["tool_input"]["command"]
        paid = not isinstance(command, str) or bool(PAID.search(command))
    except Exception:  # unreadable payload: ask rather than let it through
        paid = True
    if paid:
        print(json.dumps(ASK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
