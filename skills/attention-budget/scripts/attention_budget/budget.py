"""Per-kind word budgets and style limits. TOML, read-only, stdlib."""
from __future__ import annotations

import os
import tomllib
from pathlib import Path

from .vocab import CONFIG_DIR

BUDGET_PATH = CONFIG_DIR / "budget.toml"
DEFAULT_BUDGET_TOML = """# attention-budget: what a reader is asked to read, per kind of reply.
# Words are prose words only: code blocks, tables and headers are not counted.

[words]
status = 25                      # a progress line
closure = 80                     # "I changed X; here is where"
decision = 80                    # the minimum that lets the human choose
explanation = 150                # unasked-for explanation
explanation_when_requested = 600 # the human asked why/how/explain/review/design

[style]
max_grade = 11                   # Flesch-Kincaid grade; applies at 40+ words
max_unexpanded_terms = 0         # acronyms/identifiers the reader never used and the reply did not expand
max_numbers_in_prose = 2         # numbers belong in a table or on their own line
no_headers_under_words = 500
max_em_dashes = 0

[hook]
mode = "advise"                  # "advise": correct on the next prompt. "block": refuse to stop once, with a reason.
"""


def load(path: Path | None = None) -> dict:
    p = path or BUDGET_PATH
    try:
        return tomllib.loads(Path(p).read_text())
    except OSError:
        return tomllib.loads(DEFAULT_BUDGET_TOML)


def init(path: Path | None = None) -> Path:
    p = path or BUDGET_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text(DEFAULT_BUDGET_TOML)
    return p
