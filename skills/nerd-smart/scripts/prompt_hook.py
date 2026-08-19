#!/usr/bin/env python3
"""Inject standing user authorization to invoke Nerd routing and Memory."""

from __future__ import annotations

import argparse
import json
import sys


INSTRUCTION = (
    "Always invoke the installed `nerd-smart` skill before substantive work on "
    "every user request. Follow its Focus Record and endpoint contract. "
    "Automatically activate the installed `nerd-memory` skill for the current "
    "user-workspace namespace on every request, after building Smart's "
    "memory-blind Focus Record and endpoint. This standing authorization permits "
    "only namespace-scoped local reads and non-destructive Memory writes; it never "
    "confirms remembered changes or authorizes actions. No hook authorizes "
    "combining Nerd with Superpowers, Ponytail, or Caveman; only an explicit "
    "user request in the current prompt authorizes that pairing."
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--agent",
        required=True,
        choices=("claude-code", "codex", "cursor"),
    )
    args = parser.parse_args()
    sys.stdin.read()

    if args.agent == "cursor":
        payload = {"additional_context": INSTRUCTION}
    else:
        payload = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": INSTRUCTION,
            }
        }

    print(json.dumps(payload, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
