"""Read agent transcripts from every harness found. One function per harness."""
from __future__ import annotations

import glob
import json
import os
import sqlite3
from dataclasses import dataclass
from typing import Iterator

import os as _os

# Globs can be extended via env vars (colon-separated) so imported archives are scanned
# without editing code, e.g. an rsync'd copy of another machine's sessions.
CLAUDE_GLOB = "~/.claude/projects/*/*.jsonl"
CODEX_GLOB = "~/.codex/sessions/*/*/*/rollout-*.jsonl"
HERMES_DB = "~/.hermes/state.db"

def _extra(var: str) -> list[str]:
    return [p for p in _os.environ.get(var, "").split(":") if p.strip()]

CLAUDE_GLOBS = [CLAUDE_GLOB] + _extra("ATTENTION_BUDGET_CLAUDE_GLOBS")
CODEX_GLOBS = [CODEX_GLOB] + _extra("ATTENTION_BUDGET_CODEX_GLOBS")

SOURCES = ("claude", "codex", "hermes")


@dataclass
class Msg:
    role: str          # "user" | "assistant"
    text: str
    ts: str            # ISO timestamp or ""
    session: str
    source: str = "claude"


def _blocks_text(content, text_types=("text", "input_text", "output_text")) -> tuple[str, bool]:
    """(joined text, contains a tool_result block)"""
    if isinstance(content, str):
        return content, False
    if isinstance(content, list):
        texts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") in text_types]
        is_tool = any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)
        return "\n".join(t for t in texts if t), is_tool
    return "", False


def _human(text: str) -> bool:
    """Harness-injected user turns start with a tag; a person's message does not."""
    return bool(text.strip()) and not text.lstrip().startswith("<")


def iter_claude(path: str) -> Iterator[Msg]:
    session = os.path.splitext(os.path.basename(path))[0]
    try:
        fh = open(path, errors="ignore")
    except OSError:
        return
    with fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            t = d.get("type")
            if t not in ("user", "assistant"):
                continue
            text, is_tool = _blocks_text(d.get("message", {}).get("content"))
            if not text.strip() or (t == "user" and (is_tool or not _human(text))):
                continue
            yield Msg(t, text, d.get("timestamp", "") or "", session, "claude")


def iter_codex(path: str) -> Iterator[Msg]:
    session = os.path.basename(path).replace("rollout-", "").replace(".jsonl", "")
    try:
        fh = open(path, errors="ignore")
    except OSError:
        return
    with fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") != "response_item":
                continue
            p = d.get("payload") or {}
            if p.get("type") != "message" or p.get("role") not in ("user", "assistant"):
                continue
            text, _ = _blocks_text(p.get("content"))
            if not text.strip() or (p["role"] == "user" and not _human(text)):
                continue
            yield Msg(p["role"], text, d.get("timestamp", "") or "", session, "codex")


def iter_hermes(db_path: str = HERMES_DB) -> Iterator[Msg]:
    p = os.path.expanduser(db_path)
    if not os.path.exists(p):
        return
    try:
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        rows = con.execute(
            "SELECT role, content, timestamp, session_id FROM messages "
            "WHERE role IN ('user','assistant') AND content IS NOT NULL ORDER BY session_id, timestamp"
        )
        for role, content, ts, sid in rows:
            text = content if isinstance(content, str) else ""
            if not text.strip() or (role == "user" and not _human(text)):
                continue
            iso = ""
            try:
                from datetime import datetime, timezone
                iso = datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
            except (TypeError, ValueError):
                pass
            yield Msg(role, text, iso, str(sid), "hermes")
        con.close()
    except sqlite3.Error:
        return


def iter_many(sources: tuple[str, ...] = SOURCES, claude_glob: str = CLAUDE_GLOB,
              codex_glob: str = CODEX_GLOB, hermes_db: str = HERMES_DB) -> Iterator[Msg]:
    if "claude" in sources:
        globs = CLAUDE_GLOBS if claude_glob == CLAUDE_GLOB else [claude_glob]
        for g in globs:
            for path in sorted(glob.glob(os.path.expanduser(g))):
                yield from iter_claude(path)
    if "codex" in sources:
        globs = CODEX_GLOBS if codex_glob == CODEX_GLOB else [codex_glob]
        for g in globs:
            for path in sorted(glob.glob(os.path.expanduser(g))):
                yield from iter_codex(path)
    if "hermes" in sources:
        yield from iter_hermes(hermes_db)


def last_exchange(path: str) -> tuple[str | None, str | None]:
    """(last human prompt, last assistant text) from one Claude Code or Codex transcript."""
    reader = iter_codex if os.path.basename(path).startswith("rollout-") else iter_claude
    last_user = None
    last_assistant = None
    for m in reader(path):
        if m.role == "user":
            last_user, last_assistant = m.text, None
        else:
            last_assistant = m.text
    return last_user, last_assistant
