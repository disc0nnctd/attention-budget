"""Measure one agent reply. Pure functions over text; no I/O, no network, no LLM."""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

# ---------------------------------------------------------------- text shapes
FENCE_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
TABLE_LINE_RE = re.compile(r"^\s*\|.*\|\s*$", re.M)
HEADER_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S.*$", re.M)
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S", re.M)
BOLD_RE = re.compile(r"\*\*[^*\n]+\*\*")
EM_DASH_RE = re.compile(r"—|\s--\s")
PAREN_RE = re.compile(r"\([^()\n]{3,}\)")
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
NUM_RE = re.compile(r"(?<![\w/.\-])[$₹€£]?\d[\d,]*(?:\.\d+)?%?(?![\w/])")
ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,6}\b")
IDENT_RE = re.compile(
    r"(?<![\w/])(?:"
    r"[a-z]+_[a-z0-9_]+"                 # snake_case
    r"|[a-z]+(?:[A-Z][a-z0-9]+)+"       # camelCase
    r"|[a-z][a-z0-9]*\.[a-z][a-z0-9_.]+" # dotted.name
    r"|--?[a-z][a-z0-9\-]{2,}"           # --flag
    r")(?![\w/])"
)
PATH_RE = re.compile(r"(?:^|[\s(`\"'])(?:~|\.{0,2}/)?[\w.\-]+(?:/[\w.\-]+)+|\b[\w\-]+\.(?:py|md|toml|json|yaml|yml|sh|ts|js|rs|go|txt|sql|html|css)\b")
CHANGE_VERB_RE = re.compile(
    r"\b(?:wrote|written|creat(?:ed|es)|updat(?:ed|es)|chang(?:ed|es)|committ?ed|pushed|delet(?:ed|es)|"
    r"renam(?:ed|es)|install(?:ed|s)|fix(?:ed|es)|add(?:ed|s)|remov(?:ed|es)|mov(?:ed|es)|edit(?:ed|s)|"
    r"patch(?:ed|es)|appli(?:ed|es)|deploy(?:ed|s)|done|complet(?:ed|e)|sav(?:ed|es)|filed)\b",
    re.I,
)
QUESTION_RE = re.compile(
    r"\?\s*$|\b(?:do you want|would you like|should i|shall i|which (?:of|one|do)|let me know|your call|"
    r"confirm|can you (?:tell|share|confirm)|do you (?:prefer|need)|pick one|choose)\b",
    re.I | re.M,
)
REQUESTED_RE = re.compile(
    r"\b(?:explain|why|how (?:does|do|did|would|should|is|are)|walk me through|meditate|think (?:about|through)|"
    r"analy[sz]e|analysis|review|design|compare|what do you think|thoughts|deep dive|elaborate|in detail|"
    r"teach|understand|research|summari[sz]e|write ?up|document|plan|proposal|options)\b",
    re.I,
)
BARE_REAUTH = {
    "continue", "continue.", "continue from where you left off", "yes", "y", "ok", "okay", "go", "go ahead",
    "proceed", "do it", "sure", "yes please", "k", "carry on", "keep going", "next",
}

KINDS = ("decision", "status", "closure", "explanation")


def strip_code(text: str) -> str:
    text = FENCE_RE.sub(" ", text)
    text = INLINE_CODE_RE.sub(" ", text)
    return text


def prose_only(text: str) -> str:
    """Text the reader must actually read as sentences: no code, no tables, no headers."""
    t = strip_code(text)
    t = TABLE_LINE_RE.sub(" ", t)
    t = HEADER_RE.sub(" ", t)
    return t


def sentences(prose: str) -> list[str]:
    """Sentences the reader must parse. A line break ends a sentence: bullets and bare lines count."""
    out: list[str] = []
    for line in prose.split("\n"):
        line = line.strip()
        if not line:
            continue
        out.extend(p.strip() for p in SENT_SPLIT_RE.split(line) if p.strip())
    return [p for p in out if WORD_RE.search(p)]


def syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def fk_grade(prose: str) -> float:
    sents = sentences(prose)
    words = WORD_RE.findall(prose)
    if not sents or not words:
        return 0.0
    syl = sum(syllables(w) for w in words)
    return round(0.39 * (len(words) / len(sents)) + 11.8 * (syl / len(words)) - 15.59, 1)


def is_bare_reauth(user_text: str) -> bool:
    return user_text.strip().lower().rstrip(".!") in {s.rstrip(".") for s in BARE_REAUTH}


def is_requested(user_text: str | None) -> bool:
    """Did the human ask for an explanation-shaped reply?"""
    return bool(user_text) and bool(REQUESTED_RE.search(user_text))


# ------------------------------------------------------------------- terms
def candidate_terms(prose: str) -> list[str]:
    """Acronyms and identifiers in prose: the tokens that read as jargon."""
    out: list[str] = []
    for m in ACRONYM_RE.finditer(prose):
        t = m.group(0)
        if t in ("I", "A"):
            continue
        out.append(t)
    out.extend(m.group(0) for m in IDENT_RE.finditer(prose))
    return out


def expanded_on_first_use(term: str, prose: str) -> bool:
    """`term (Some Expansion)` or `Some Expansion (term)` within the same sentence, first occurrence."""
    i = prose.find(term)
    if i < 0:
        return False
    # sentence window around first occurrence
    start = max(prose.rfind(".", 0, i), prose.rfind("\n", 0, i), 0)
    end_candidates = [x for x in (prose.find(".", i), prose.find("\n", i)) if x >= 0]
    end = min(end_candidates) if end_candidates else len(prose)
    window = prose[start:end + 1]
    return bool(re.search(re.escape(term) + r"\s*\(", window)) or bool(re.search(r"\(\s*" + re.escape(term) + r"\s*\)", window))


def unexpanded_terms(prose: str, vocab: set[str]) -> list[str]:
    seen: list[str] = []
    for t in candidate_terms(prose):
        key = t.lower().lstrip("-")
        if key in vocab or t in seen:
            continue
        if expanded_on_first_use(t, prose):
            continue
        seen.append(t)
    return seen


def invented_names(prose: str, vocab: set[str]) -> list[str]:
    """Runs of two or more Capitalised Words not at sentence start and not in the reader's vocabulary."""
    found: list[str] = []
    for s in sentences(prose):
        toks = list(re.finditer(r"[A-Za-z][A-Za-z'\-]*", s))
        run: list[str] = []
        for idx, m in enumerate(toks):
            w = m.group(0)
            cap = w[0].isupper() and not w.isupper() and idx > 0
            if cap:
                run.append(w)
            else:
                if len(run) >= 2:
                    phrase = " ".join(run)
                    if phrase.lower() not in vocab and phrase not in found:
                        found.append(phrase)
                run = []
        if len(run) >= 2:
            phrase = " ".join(run)
            if phrase.lower() not in vocab and phrase not in found:
                found.append(phrase)
    return found


# ------------------------------------------------------------------- kinds
def classify(text: str) -> str:
    prose = prose_only(text)
    words = len(WORD_RE.findall(prose))
    tail = "\n".join(prose.strip().split("\n")[-6:])
    if QUESTION_RE.search(tail):
        return "decision"
    if words <= 25:
        return "status"
    if CHANGE_VERB_RE.search(prose) and PATH_RE.search(text) and words <= 120:
        return "closure"
    return "explanation"


# ------------------------------------------------------------------- result
@dataclass
class Measurement:
    kind: str
    words: int
    sentences: int
    grade: float
    headers: int
    bullets: int
    bold_runs: int
    em_dashes: int
    parentheticals: int
    numbers_in_prose: int
    code_lines: int
    unexpanded: list[str] = field(default_factory=list)
    invented: list[str] = field(default_factory=list)
    requested: bool = False
    budget_words: int = 0
    over_words: int = 0
    breaches: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def measure(text: str, vocab: set[str], budget: dict, requested: bool = False) -> Measurement:
    kind = classify(text)
    prose = prose_only(text)
    words = len(WORD_RE.findall(prose))
    sents = sentences(prose)
    code_lines = sum(block.count("\n") for block in FENCE_RE.findall(text))
    # numbers in running prose only (not in tables, lists, code)
    prose_no_lists = BULLET_RE.sub(" ", prose)
    nums = len(NUM_RE.findall(prose_no_lists))
    m = Measurement(
        kind=kind,
        words=words,
        sentences=len(sents),
        grade=fk_grade(prose),
        headers=len(HEADER_RE.findall(strip_code(text))),
        bullets=len(BULLET_RE.findall(strip_code(text))),
        bold_runs=len(BOLD_RE.findall(strip_code(text))),
        em_dashes=len(EM_DASH_RE.findall(strip_code(text))),
        parentheticals=len(PAREN_RE.findall(prose)),
        numbers_in_prose=nums,
        code_lines=code_lines,
        unexpanded=unexpanded_terms(prose, vocab),
        invented=invented_names(prose, vocab),
        requested=requested,
    )
    w = budget.get("words", {})
    if kind == "explanation" and requested:
        m.budget_words = int(w.get("explanation_when_requested", 600))
    else:
        m.budget_words = int(w.get(kind, 150))
    m.over_words = max(0, words - m.budget_words)
    style = budget.get("style", {})
    if m.over_words:
        m.breaches.append(f"{kind}: {words} words, budget {m.budget_words}")
    if m.grade > float(style.get("max_grade", 11)) and words >= 40:
        m.breaches.append(f"reading grade {m.grade}, max {style.get('max_grade', 11)}")
    if len(m.unexpanded) > int(style.get("max_unexpanded_terms", 0)):
        m.breaches.append("unexpanded terms: " + ", ".join(m.unexpanded[:6]))
    if m.numbers_in_prose > int(style.get("max_numbers_in_prose", 2)):
        m.breaches.append(f"{m.numbers_in_prose} numbers in prose, max {style.get('max_numbers_in_prose', 2)}")
    if m.headers and words < int(style.get("no_headers_under_words", 500)):
        m.breaches.append(f"{m.headers} headers in a {words}-word reply")
    if m.em_dashes > int(style.get("max_em_dashes", 0)):
        m.breaches.append(f"{m.em_dashes} em-dashes")
    return m
