# attention-budget

Skills that make an agent spend a human's attention like the scarce thing it is. Works in Claude
Code, Codex CLI, Gemini CLI, OpenCode, Hermes Agent, Cursor, and anything else that reads the
[Agent Skills](https://agentskills.io) format. Stdlib Python inside; no LLM in the measurement path.

## Install

```bash
git clone https://github.com/disc0nnctd/attention-budget ~/projects/attention-budget
~/projects/attention-budget/install.sh          # symlinks the skills into every harness found
~/projects/attention-budget/install.sh --hooks  # also prints the Claude Code hooks snippet
```

That is the whole install. The same skill directory is linked into `~/.claude/skills`,
`~/.codex/skills`, `~/.agents/skills`, `~/.gemini/skills`, `~/.hermes/skills`,
`~/.config/opencode/skills` and `~/.cursor/skills`, whichever exist. `init` builds the reader's
vocabulary from your own messages across Claude Code, Codex and Hermes transcripts.

## The two skills

**`attention-budget`** — every reply is one of four kinds with its own prose-word budget: status
(25), closure (80), decision (80), explanation (150, or 600 when you asked for it). Terms you have
never typed that the reply does not expand are counted as breaches. Numbers in prose, headers on
short replies, and em-dashes are counted. The skill tells the agent to measure any long or technical
draft with the bundled script before sending. Where the harness has hooks, a hook measures every
reply automatically.

**`decision-gates`** — when to stop and ask. Gates by reversibility and by what only the human
knows, never by "importance". Bans "continue?" prompts: a decision must state what the agent lacks,
the options, each option's reversibility and cost, and the default on silence, in under 80 words.

## Why

Agents over-explain in terms the reader never used, and every unread word is drawn from the same
budget as every "continue?" the reader has to answer. Both are the agent surfacing on its own terms,
which is also the mechanism behind human-oversight fatigue (Mitchell, Ghosh, Passi 2026, arXiv
2608.23642). The root cause of the verbosity is measured: reward models prefer longer answers
regardless of quality, so "be concise" in a prompt decays over a session. The only thing that holds
is measuring the reply after it is written and correcting on breach.

## Enforcement, weakest to strongest

1. **Skill** (all harnesses): the agent follows the budget and runs the measurer on long drafts.
2. **Advise hook** (Claude Code): on the next prompt, one line of context says what the previous
   reply breached. Nobody sees a doubled reply.
3. **Block hook** (Claude Code): the reply is refused once, with the reason, and rewritten before
   the human reads it.

Hermes (response post-processor plugin), OpenCode (plugin) and Codex adapters are the next step;
each is one file against a measurement core that already exists.

## Report

```
python3 skills/attention-budget/scripts/report.py --since 2026-06      # by month, all harnesses
python3 skills/attention-budget/scripts/report.py --by source           # Claude Code vs Codex vs Hermes
```

Columns: replies, prose words, noise (words over budget), breach rate, unexpanded terms per 1,000
words, mean reading grade, short replies with headers, em-dashes, and the share of human messages
that are a bare "continue"/"yes"/"ok" (the approval-fatigue signature from the paper).

## Layout

```
skills/attention-budget/   SKILL.md, scripts/ (measure, report, vocab, hook, init), references/
skills/decision-gates/     SKILL.md
adapters/claude-code/      the two hook scripts
install.sh                 symlink into every harness
tests/                     python3 -m unittest discover -s tests
```

## Limits

Kind classification is heuristic (questions, change verbs plus paths, length). It is right often
enough to budget by. The tool measures what the reader was asked to read; it does not judge whether
the reply was correct. It does not rewrite; the model does.

MIT.
