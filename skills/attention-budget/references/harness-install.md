# Per-harness install

The skill directory is the same everywhere. `install.sh` at the repo root symlinks it into every
harness skill directory it finds. Hard enforcement (a hook that measures every reply) exists where
the harness has hooks.

| harness | skill path | hard enforcement |
|---|---|---|
| Claude Code | `~/.claude/skills/attention-budget` | `UserPromptSubmit` hook (advise) and `Stop` hook (block). Snippet below. |
| Codex CLI | `~/.codex/skills/attention-budget` or `~/.agents/skills/` | skill only (v0) |
| Gemini CLI | `~/.gemini/skills/attention-budget` or `~/.agents/skills/` | skill only (v0) |
| OpenCode | `~/.config/opencode/skills/attention-budget` | skill only (v0); plugin adapter planned |
| Hermes Agent | `~/.hermes/skills/attention-budget` | skill only (v0); response post-processor plugin planned |
| Cursor | `~/.cursor/skills/attention-budget` | skill only |

Transcripts are read for the vocabulary and the report from Claude Code (`~/.claude/projects`),
Codex (`~/.codex/sessions`) and Hermes (`~/.hermes/state.db`). OpenCode and Gemini readers are
one function each in `scripts/attention_budget/transcripts.py`.

## Claude Code hooks

Add to `~/.claude/settings.json` (paths printed by `scripts/init.py`):

```json
{
  "hooks": {
    "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "<repo>/adapters/claude-code/claude-code-prompt.sh", "timeout": 10}]}],
    "Stop":             [{"hooks": [{"type": "command", "command": "<repo>/adapters/claude-code/claude-code-stop.sh",   "timeout": 10}]}]
  }
}
```

- **advise** (default): the prompt hook measures the previous reply from the transcript and, only on
  breach, injects one line of context so the next reply corrects. The human never sees a doubled
  reply.
- **block**: set `[hook] mode = "block"`. The stop hook measures `last_assistant_message` and, on
  breach, exits 2 with the reason once per prompt. The reply is rewritten before the human reads it.
  Both hooks log to `~/.config/attention-budget/log/measurements.jsonl`.
