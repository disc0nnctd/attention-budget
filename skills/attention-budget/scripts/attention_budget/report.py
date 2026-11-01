"""Aggregate measurements over transcripts. One table, trend by month or session."""
from __future__ import annotations

from collections import defaultdict

from .measure import measure, is_bare_reauth, is_requested, KINDS
from .transcripts import iter_many, SOURCES


def collect(vocab: set[str], budget: dict, sources: tuple[str, ...] = SOURCES, by: str = "month"):
    rows: dict[str, dict] = defaultdict(lambda: {
        "assistant_msgs": 0, "words": 0, "over_words": 0, "breaches": 0,
        "unexpanded": 0, "grade_sum": 0.0, "graded": 0, "headers_small": 0, "em_dashes": 0,
        "user_msgs": 0, "reauth": 0, **{f"words_{k}": 0 for k in KINDS}, **{f"n_{k}": 0 for k in KINDS},
    })
    last_user: dict[str, str] = {}
    for m in iter_many(sources):
        key = m.ts[:7] if by == "month" else (m.source if by == "source" else m.session)
        if not key:
            continue
        r = rows[key]
        if m.role == "user":
            r["user_msgs"] += 1
            if is_bare_reauth(m.text):
                r["reauth"] += 1
            last_user[m.session] = m.text
            continue
        mm = measure(m.text, vocab, budget, requested=is_requested(last_user.get(m.session)))
        r["assistant_msgs"] += 1
        r["words"] += mm.words
        r[f"words_{mm.kind}"] += mm.words
        r[f"n_{mm.kind}"] += 1
        r["over_words"] += mm.over_words
        r["breaches"] += 1 if mm.breaches else 0
        r["unexpanded"] += len(mm.unexpanded)
        r["em_dashes"] += mm.em_dashes
        if mm.words >= 40:
            r["grade_sum"] += mm.grade
            r["graded"] += 1
        if mm.headers and mm.words < 500:
            r["headers_small"] += 1
    return dict(sorted(rows.items()))


def render(rows: dict[str, dict]) -> str:
    head = (f"{'period':<10}{'msgs':>6}{'words':>8}{'noise':>8}{'noise%':>7}{'breach%':>8}"
            f"{'terms/1k':>9}{'grade':>7}{'hdr<500':>8}{'dash':>6}{'continue%':>10}")
    lines = [head, "-" * len(head)]
    for k, r in rows.items():
        if not r["assistant_msgs"] and not r["user_msgs"]:
            continue
        words = r["words"] or 1
        grade = r["grade_sum"] / r["graded"] if r["graded"] else 0.0
        cont = 100.0 * r["reauth"] / r["user_msgs"] if r["user_msgs"] else 0.0
        lines.append(
            f"{k:<10}{r['assistant_msgs']:>6}{r['words']:>8}{r['over_words']:>8}"
            f"{100.0 * r['over_words'] / words:>6.0f}%"
            f"{100.0 * r['breaches'] / max(1, r['assistant_msgs']):>7.0f}%"
            f"{1000.0 * r['unexpanded'] / words:>9.1f}{grade:>7.1f}{r['headers_small']:>8}{r['em_dashes']:>6}"
            f"{cont:>9.0f}%"
        )
    lines.append("")
    lines.append("noise = prose words over the per-kind budget · terms/1k = unexpanded terms per 1,000 prose words")
    lines.append("grade = mean Flesch-Kincaid grade of replies with 40+ words · continue% = bare re-authorisations among human messages")
    return "\n".join(lines)


def kinds_breakdown(rows: dict[str, dict]) -> str:
    tot = defaultdict(int)
    for r in rows.values():
        for k in KINDS:
            tot[f"n_{k}"] += r[f"n_{k}"]
            tot[f"words_{k}"] += r[f"words_{k}"]
    out = [f"{'kind':<13}{'msgs':>7}{'words':>9}{'avg':>6}"]
    for k in KINDS:
        n = tot[f"n_{k}"]
        out.append(f"{k:<13}{n:>7}{tot[f'words_{k}']:>9}{(tot[f'words_{k}'] / n if n else 0):>6.0f}")
    return "\n".join(out)
