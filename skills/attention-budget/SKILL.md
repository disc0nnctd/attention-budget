---
name: attention-budget
description: Keep replies to a human within a per-kind word budget and in the reader's own vocabulary. Use on every reply, and always before sending anything over about 80 words, an explanation, a summary, a report of completed work, or a question to the user. Also use when the user says the agent is too verbose, over-explains, uses jargon, or asks for shorter or plainer replies. Bundles a stdlib Python measurer that classifies a draft, counts prose words against budget, and lists unexpanded terms.
license: MIT
metadata:
  author: attention-budget
  version: "0.1"
---

# attention-budget

The human's attention is one account. Every word draws from it. A reply is not better because it is
longer, and a term the reader never used is a small decision they must make before they can continue.
This skill meters the words. Enforcement is measured after writing, not requested in a prompt.

## 1. Decide the kind before writing

| kind | what it is | budget (prose words) |
|---|---|---|
| **status** | one line on what you are doing | 25 |
| **closure** | you changed something: what, where, how it was verified | 80 |
| **decision** | you need something only the human has | 80 |
| **explanation** | the human did not ask for it | 150 |
| **explanation, requested** | the human asked why, how, explain, review, design, compare, analyse | 600 |

Prose words only. Code blocks, tables and headers are free. Silence is a valid reply: if nothing
changed and nothing is needed, say nothing or one line.

## 2. Write within it

- Lead with the answer or the outcome. Cut by leaving things out, not by packing sentences tighter.
- Use only terms the reader has used. Expand any other acronym or identifier on first use, once, or
  drop it. Never coin a name for something during the task and then refer to it by that name.
- Numbers go in a table or on their own line, never inside a sentence, and only if they change what
  the reader does.
- No headers under 500 words. No em-dashes. Bullets for parallel items, prose for an argument.
- A **decision** states what you lack, the options, each option's reversibility and cost, and what
  you will do if the human says nothing. Never ask only "continue?".
- A **closure** names the file or place, what changed, and what verified it. Nothing else.

## 3. Measure the draft when it is long or technical

If the draft is over 80 words, or contains acronyms or identifiers, write it to a temp file and run:

```
python3 <skill-dir>/scripts/measure.py /tmp/draft.md            # add --requested if the human asked for an explanation
```

Output is one line plus any breaches: `kind`, `words/budget`, reading `grade`, `unexpanded` terms,
`invented` names, headers, numbers in prose. Fix every breach and send. Re-run at most once.
If the harness has the hook installed (see [references/harness-install.md](references/harness-install.md))
the measurement runs automatically and you need not run it by hand.

## 4. Vocabulary

The reader's vocabulary is built from their own messages across every harness on the machine
(Claude Code, Codex, Hermes), plus a small seed of universal terms.

```
python3 <skill-dir>/scripts/vocab.py build          # once; rebuild occasionally
python3 <skill-dir>/scripts/vocab.py add HNSW RLS   # when the user uses a term you will reuse
```

A term the reader has typed is known. Anything else acronym- or identifier-shaped is unexpanded
unless the draft expands it on first use.

## 5. Trend

```
python3 <skill-dir>/scripts/report.py --since 2026-07          # by month, all harnesses
python3 <skill-dir>/scripts/report.py --by source              # Claude Code vs Codex vs Hermes
```

Reports prose words, noise (words over budget), breach rate, unexpanded terms per 1,000 words,
mean reading grade, and the share of human messages that are a bare "continue" or "yes", which is
the approval-fatigue signature.

## Example

Before (explanation, 96 words, 3 unexpanded terms):

> I went ahead and refactored the retrieval path so that the HNSW index is consulted before the
> BM25 fallback, which should improve recall on long-tail queries because the ANN step now returns
> candidates that the lexical stage previously missed; I also updated the RLS policy so that...

After (closure, 31 words):

> Changed `search/retrieve.py`: the vector index now runs before the keyword fallback. Recall on
> rare queries should rise. Row-level security (RLS) policy updated to match. Tests pass.

Budgets live in `~/.config/attention-budget/budget.toml`; see [references/budgets.md](references/budgets.md).
