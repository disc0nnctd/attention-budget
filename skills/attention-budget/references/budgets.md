# Budgets and why

`~/.config/attention-budget/budget.toml` (created by `scripts/init.py`):

```toml
[words]
status = 25
closure = 80
decision = 80
explanation = 150
explanation_when_requested = 600

[style]
max_grade = 11               # Flesch-Kincaid grade, applied to replies with 40+ words
max_unexpanded_terms = 0
max_numbers_in_prose = 2
no_headers_under_words = 500
max_em_dashes = 0

[hook]
mode = "advise"              # or "block"
```

## Rationale

- **Per kind, not per message.** A decision that needs 80 words and a status line that needs 8 are
  not the same object. One budget for both is either too loose or too tight.
- **Requested explanation gets four times the budget.** The reader asked. The cost is still real, so
  it is not unlimited.
- **Unexpanded terms are the terminology-fatigue measure.** Each is a micro-decision for the reader.
  The vocabulary is built from the reader's own messages, so "jargon" means "words this reader has
  not used", not a fixed list.
- **Reading grade 11** is the level of a serious newspaper. Technical replies routinely measure 14+
  because of long noun phrases, and the fix is shorter sentences, not simpler ideas.
- **Numbers out of prose.** A number inside a sentence is skimmed; on its own line it is read.
- **No headers under 500 words.** Headers on a short reply are structure without content.

## Why measured, not prompted

Reward models prefer longer answers regardless of quality (Park et al. 2024, arXiv 2403.19159;
ACL 2026 arXiv 2505.12843; AAAI arXiv 2511.12573; arXiv 2603.10535 on length inflation under RL).
A "be concise" rule in the prompt decays over a session because the model drifts back toward what
its reward model liked. Measuring the last reply and correcting on breach holds because it does not
depend on the model remembering.
