"""read_note must say when it truncated, and let the caller read the rest (review #5, 2026-10-04).

The tool promised "the full content" but returned text[:20_000] with only path +
content, so an agent missed later corrections in long notes believing it had read
everything (in the reviewed vault: 15 Knowledge, 53 Daily, 17 Logs notes over the
cap).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "integrations" / "obsidian-mcp-server"))

import server  # noqa: E402,F401  (registers the tool; its docstring is checked below)
import vault_ops  # noqa: E402

TAIL = "TAIL-MARKER-correction-at-the-end"


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    v = tmp_path / "vault"
    v.mkdir()
    monkeypatch.setenv(vault_ops._VAULT_ENV, str(v))
    monkeypatch.setattr(vault_ops, "_USAGE_LOG", None, raising=False)
    return v


def test_long_note_flags_truncation_and_the_tail_is_reachable(vault):
    text = "x" * (vault_ops._READ_CAP + 13) + TAIL
    (vault / "long.md").write_text(text, encoding="utf-8")

    first = vault_ops.read_note("long.md")
    assert first["truncated"] is True, first.keys()
    assert first["total_chars"] == len(text)
    assert TAIL not in first["content"]

    pieces, page = [first["content"]], first
    while page.get("truncated"):
        page = vault_ops.read_note("long.md", offset=page["next_offset"])
        pieces.append(page["content"])
    assert "".join(pieces) == text, "paging did not reproduce the note exactly"


def test_short_note_is_whole_and_says_so(vault):
    (vault / "short.md").write_text("hello", encoding="utf-8")
    out = vault_ops.read_note("short.md")
    assert out["content"] == "hello"
    assert out["truncated"] is False and out["total_chars"] == 5
    assert out.get("next_offset") is None


def test_bad_offset_is_an_error_not_an_empty_page(vault):
    (vault / "short.md").write_text("hello", encoding="utf-8")
    assert "error" in vault_ops.read_note("short.md", offset=-1)
    assert "error" in vault_ops.read_note("short.md", offset=99)


def test_tool_description_no_longer_promises_the_full_note():
    doc = server.obsidian_read_note.__doc__ or ""
    if not doc and hasattr(server.obsidian_read_note, "fn"):
        doc = server.obsidian_read_note.fn.__doc__ or ""
    assert "truncated" in doc and "offset" in doc, doc
