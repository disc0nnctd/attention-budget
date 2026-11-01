"""attention-budget command line and hook entry points."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import budget as budget_mod
from . import vocab as vocab_mod
from .measure import measure, is_requested
from .report import collect, render, kinds_breakdown
from .transcripts import SOURCES, last_exchange


def _ctx(args):
    return vocab_mod.load(Path(args.vocab) if getattr(args, "vocab", None) else None), \
        budget_mod.load(Path(args.budget) if getattr(args, "budget", None) else None)


def cmd_measure(args) -> int:
    vocab, budget = _ctx(args)
    text = Path(args.file).read_text() if args.file and args.file != "-" else sys.stdin.read()
    m = measure(text, vocab, budget, requested=args.requested)
    if args.json:
        print(json.dumps(m.as_dict(), indent=2))
    else:
        print(f"kind={m.kind} words={m.words}/{m.budget_words} grade={m.grade} unexpanded={m.unexpanded} "
              f"invented={m.invented} headers={m.headers} numbers_in_prose={m.numbers_in_prose} em_dashes={m.em_dashes}")
        for b in m.breaches:
            print("  breach:", b)
    return 1 if m.breaches and args.strict else 0


def cmd_vocab(args) -> int:
    if args.action == "build":
        terms = vocab_mod.build(tuple(args.sources), extra=args.add or [])
        p = vocab_mod.save(terms, Path(args.out) if args.out else None)
        print(f"{len(terms)} terms written to {p}")
        return 0
    if args.action == "show":
        for t in sorted(vocab_mod.load(Path(args.out) if args.out else None)):
            print(t)
        return 0
    if args.action == "add":
        v = vocab_mod.load()
        v.update(t.lower() for t in args.add or [])
        # keep the seed out of the user file
        seed = set(l.strip().lower() for l in vocab_mod.SEED_PATH.read_text().splitlines() if l.strip() and not l.startswith("#"))
        vocab_mod.save(v - seed)
        print(f"added {len(args.add or [])}; {len(v)} terms known")
        return 0
    return 2


def cmd_report(args) -> int:
    vocab, budget = _ctx(args)
    rows = collect(vocab, budget, sources=tuple(args.sources), by=args.by)
    if args.since:
        rows = {k: v for k, v in rows.items() if k >= args.since}
    print(render(rows))
    print()
    print(kinds_breakdown(rows))
    return 0


def _reason(m) -> str:
    what = "; ".join(m.breaches)
    fix = []
    if m.over_words:
        fix.append(f"cut to {m.budget_words} words by leaving things out")
    if m.unexpanded:
        fix.append("expand each listed term on first use or drop it")
    if m.numbers_in_prose > 2:
        fix.append("move numbers into a table or their own line")
    if m.headers and m.words < 500:
        fix.append("remove the headers")
    return f"Reply over attention budget ({what}). Keep the answer; {'; '.join(fix)}."


def cmd_hook(args) -> int:
    vocab, budget = _ctx(args)
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    mode = budget.get("hook", {}).get("mode", "advise")
    log_dir = vocab_mod.CONFIG_DIR / "log"
    log_dir.mkdir(parents=True, exist_ok=True)

    if args.event == "stop":
        text = payload.get("last_assistant_message") or ""
        if not text.strip():
            return 0
        user_text, _ = last_exchange(payload.get("transcript_path", "")) if payload.get("transcript_path") else (None, None)
        m = measure(text, vocab, budget, requested=is_requested(user_text))
        with open(log_dir / "measurements.jsonl", "a") as fh:
            fh.write(json.dumps({"session": payload.get("session_id"), "prompt": payload.get("prompt_id"), **m.as_dict()}) + "\n")
        if not m.breaches or mode != "block" or payload.get("stop_hook_active"):
            return 0
        marker = log_dir / f"blocked-{payload.get('session_id')}-{payload.get('prompt_id')}"
        if marker.exists():
            return 0
        marker.touch()
        reason = _reason(m)
        print(json.dumps({"decision": "block", "reason": reason,
                          "hookSpecificOutput": {"hookEventName": "Stop", "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}))
        return 2

    if args.event == "prompt":
        path = payload.get("transcript_path", "")
        if not path or not os.path.exists(path):
            return 0
        user_text, assistant_text = last_exchange(path)
        if not assistant_text:
            return 0
        m = measure(assistant_text, vocab, budget, requested=is_requested(user_text))
        if not m.breaches:
            return 0
        ctx = ("attention-budget: your previous reply was over budget (" + "; ".join(m.breaches) +
               "). For this reply: " + _reason(m).split("Keep the answer; ", 1)[-1])
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ctx}}))
        return 0
    return 0


def cmd_init(args) -> int:
    bp = budget_mod.init()
    vp = vocab_mod.VOCAB_PATH
    if not vp.exists():
        terms = vocab_mod.build(tuple(args.sources))
        vocab_mod.save(terms)
        print(f"vocab: {len(terms)} terms from your own messages -> {vp}")
    else:
        print(f"vocab: exists at {vp}")
    print(f"budget: {bp}")
    here = Path(__file__).resolve().parents[3] / "adapters" / "claude-code"
    print("\nClaude Code (advise mode, corrects on the next prompt) — add to ~/.claude/settings.json hooks:")
    print(json.dumps({"UserPromptSubmit": [{"hooks": [{"type": "command", "command": f"{here}/claude-code-prompt.sh", "timeout": 10}]}]}, indent=2))
    print("\nOptional Stop hook (set [hook] mode = \"block\" in budget.toml to refuse once with a reason):")
    print(json.dumps({"Stop": [{"hooks": [{"type": "command", "command": f"{here}/claude-code-stop.sh", "timeout": 10}]}]}, indent=2))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="attention-budget", description=__doc__)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--vocab", help="vocab file (default ~/.config/attention-budget/vocab.txt)")
    common.add_argument("--budget", help="budget.toml (default ~/.config/attention-budget/budget.toml)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("measure", parents=[common], help="measure one reply from a file or stdin")
    s.add_argument("file", nargs="?", default="-")
    s.add_argument("--requested", action="store_true", help="the human asked for an explanation")
    s.add_argument("--json", action="store_true")
    s.add_argument("--strict", action="store_true", help="exit 1 on any breach")
    s.set_defaults(fn=cmd_measure)

    s = sub.add_parser("vocab", parents=[common], help="build or show the reader's vocabulary")
    s.add_argument("action", choices=["build", "show", "add"])
    s.add_argument("--sources", nargs="*", default=list(SOURCES), choices=SOURCES)
    s.add_argument("--add", nargs="*")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_vocab)

    s = sub.add_parser("report", parents=[common], help="trend over transcripts")
    s.add_argument("--sources", nargs="*", default=list(SOURCES), choices=SOURCES)
    s.add_argument("--by", choices=["month", "session", "source"], default="month")
    s.add_argument("--since")
    s.set_defaults(fn=cmd_report)

    s = sub.add_parser("hook", parents=[common], help="hook entry point; reads the harness JSON on stdin")
    s.add_argument("event", choices=["stop", "prompt"])
    s.set_defaults(fn=cmd_hook)

    s = sub.add_parser("init", parents=[common], help="write default budget and vocab; print the settings.json snippet")
    s.add_argument("--sources", nargs="*", default=list(SOURCES), choices=SOURCES)
    s.set_defaults(fn=cmd_init)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
