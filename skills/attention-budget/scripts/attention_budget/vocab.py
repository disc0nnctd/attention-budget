"""The reader's vocabulary: terms the human has used themselves. Built from their own messages."""
from __future__ import annotations

import os
from pathlib import Path

from .measure import candidate_terms
from .transcripts import iter_many, SOURCES

CONFIG_DIR = Path(os.environ.get("ATTENTION_BUDGET_HOME", os.path.expanduser("~/.config/attention-budget")))
VOCAB_PATH = CONFIG_DIR / "vocab.txt"
SEED_PATH = Path(__file__).with_name("seed_vocab.txt")


def load(path: Path | None = None) -> set[str]:
    out: set[str] = set()
    for p in (SEED_PATH, path or VOCAB_PATH):
        try:
            for line in Path(p).read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    out.add(line.lower())
        except OSError:
            pass
    return out


def build(sources: tuple[str, ...] = SOURCES, extra: list[str] | None = None) -> set[str]:
    terms: set[str] = set()
    for m in iter_many(sources):
        if m.role != "user":
            continue
        for t in candidate_terms(m.text):
            terms.add(t.lower().lstrip("-"))
    for t in extra or []:
        terms.add(t.lower())
    return terms


def save(terms: set[str], path: Path | None = None) -> Path:
    p = path or VOCAB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# terms the reader has used; one per line; lowercase\n" + "\n".join(sorted(terms)) + "\n")
    return p
