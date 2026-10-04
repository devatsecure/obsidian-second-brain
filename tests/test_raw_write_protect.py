"""raw/ is immutable: the MCP update tool must refuse to write there (review #3, 2026-10-04).

update_note guarded vault containment and _SKIP_DIRS, but `raw` was in neither, so
`update_note('raw/x.md', append=...)` rewrote an immutable source. Search
de-weighting raw/ is not write protection.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "integrations" / "obsidian-mcp-server"))

import vault_ops  # noqa: E402

BODY = "---\ntype: source\n---\n\noriginal source text\n"


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    v = tmp_path / "vault"
    v.mkdir()
    monkeypatch.setenv(vault_ops._VAULT_ENV, str(v))
    return v


@pytest.mark.parametrize("rel", ["raw/source.md", "raw/sub/source.md", "Raw/source.md"])
def test_update_note_refuses_raw(vault, rel):
    p = vault / rel
    p.parent.mkdir(parents=True)
    p.write_text(BODY, encoding="utf-8")
    out = vault_ops.update_note(rel, append="tampered")
    assert "error" in out, out
    assert p.read_text(encoding="utf-8") == BODY, "raw source was modified"


def test_update_note_still_edits_ordinary_notes(vault):
    p = vault / "Knowledge" / "note.md"
    p.parent.mkdir()
    p.write_text(BODY, encoding="utf-8")
    out = vault_ops.update_note("Knowledge/note.md", append="added")
    assert out.get("updated") == "Knowledge/note.md", out
    assert "added" in p.read_text(encoding="utf-8")


def test_a_file_merely_named_raw_is_not_protected(vault):
    p = vault / "Knowledge" / "raw.md"
    p.parent.mkdir()
    p.write_text(BODY, encoding="utf-8")
    assert "updated" in vault_ops.update_note("Knowledge/raw.md", append="ok")
