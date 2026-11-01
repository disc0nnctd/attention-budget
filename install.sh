#!/usr/bin/env bash
# Symlink the skills into every harness skill directory on this machine.
#   ./install.sh            link into harnesses that are installed (their config dir exists)
#   ./install.sh --all      create every known skill directory and link into all of them
#   ./install.sh --hooks    also print the Claude Code hooks snippet (never edits settings.json)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
all=0; hooks=0
for a in "$@"; do case "$a" in --all) all=1;; --hooks) hooks=1;; esac; done

# skill dir -> harness config dir whose presence means "installed"
declare -A targets=(
  ["$HOME/.claude/skills"]="$HOME/.claude"
  ["$HOME/.codex/skills"]="$HOME/.codex"
  ["$HOME/.agents/skills"]="$HOME/.agents"           # shared alias read by Gemini CLI, Codex and others
  ["$HOME/.gemini/skills"]="$HOME/.gemini"
  ["$HOME/.hermes/skills"]="$HOME/.hermes"
  ["$HOME/.config/opencode/skills"]="$HOME/.config/opencode"
  ["$HOME/.cursor/skills"]="$HOME/.cursor"
)
linked=0
for dir in "${!targets[@]}"; do
  parent="${targets[$dir]}"
  if [ "$all" = 1 ] || [ -d "$parent" ]; then
    mkdir -p "$dir"
    for skill in "$here"/skills/*/; do
      name="$(basename "$skill")"
      ln -sfn "$skill" "$dir/$name"
      echo "linked  $dir/$name"
      linked=$((linked+1))
    done
  fi
done
[ "$linked" = 0 ] && echo "no harness config directories found; use --all to create them" && exit 1

python3 "$here/skills/attention-budget/scripts/init.py" >/dev/null && echo "config  ~/.config/attention-budget/{budget.toml,vocab.txt}"
if [ "$hooks" = 1 ]; then
  echo; echo "Claude Code hooks (add to ~/.claude/settings.json):"
  python3 "$here/skills/attention-budget/scripts/init.py" | sed -n '/Claude Code/,$p'
fi
