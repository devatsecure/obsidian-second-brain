"""save_note must never replace an existing note (review #4, 2026-10-04).

The filename is `<date> - <slug(title)>.md` and the write was an unconditional
write_text, so two same-day saves with the same title (or titles that slug the
same, or captures whose first 60 chars match) silently lost the first body.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "integrations" / "obsidian-mcp-server"))

import vault_ops  # noqa: E402


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    v = tmp_path / "vault"
    v.mkdir()
    monkeypatch.setenv(vault_ops._VAULT_ENV, str(v))
    return v


def _bodies(vault):
    return sorted(p.read_text(encoding="utf-8") for p in (vault / vault_ops._NOTES_DIR).glob("*.md"))


def test_same_title_twice_keeps_both(vault):
    a = vault_ops.save_note("Standup", "first body")
    b = vault_ops.save_note("Standup", "second body")
    assert a["saved"] != b["saved"], (a, b)
    texts = _bodies(vault)
    assert any("first body" in t for t in texts), "the first save was overwritten"
    assert any("second body" in t for t in texts)


def test_titles_that_slug_the_same_keep_both(vault):
    vault_ops.save_note("Q3 plan!", "alpha")
    vault_ops.save_note("Q3 plan?", "beta")
    texts = _bodies(vault)
    assert any("alpha" in t for t in texts) and any("beta" in t for t in texts)


def test_captures_with_the_same_first_line_keep_both(vault):
    vault_ops.capture_idea("same opening line\nidea one")
    vault_ops.capture_idea("same opening line\nidea two")
    texts = _bodies(vault)
    assert any("idea one" in t for t in texts) and any("idea two" in t for t in texts)


def test_third_collision_gets_its_own_name(vault):
    paths = {vault_ops.save_note("Same", f"body {i}")["saved"] for i in range(3)}
    assert len(paths) == 3, paths
