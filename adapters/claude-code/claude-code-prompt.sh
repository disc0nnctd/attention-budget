#!/usr/bin/env bash
# Claude Code UserPromptSubmit hook (advise mode): if the previous reply was over budget,
# the next reply starts with a one-line correction in context. Reads the hook JSON on stdin.
here="$(cd "$(dirname "$0")/../.." && pwd)"
exec python3 "$here/skills/attention-budget/scripts/hook.py" prompt
