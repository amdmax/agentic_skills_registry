#!/usr/bin/env python3
"""Blocks direct git push to main/master. PreToolUse hook on Bash."""

import json
import re
import sys

data = json.load(sys.stdin)
command = data.get("tool_input", data).get("command", "")

if re.search(r"git push", command) and re.search(
    r"(origin\s+main|origin\s+master|-u\s+origin\s+main|-u\s+origin\s+master|origin\s+HEAD)",
    command,
):
    print("Direct push to main/master is blocked. Create a feature branch and open a PR instead.")
    sys.exit(2)
