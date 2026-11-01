#!/usr/bin/env bash
# Claude Code Stop hook (block mode when [hook] mode = "block"): measures the reply; refuses to
# stop once, with the breach as the reason. Reads the hook JSON on stdin.
here="$(cd "$(dirname "$0")/../.." && pwd)"
exec python3 "$here/skills/attention-budget/scripts/hook.py" stop
