import os, tempfile, importlib.util, pathlib

spec = importlib.util.spec_from_file_location(
    "lint", os.path.join(os.path.dirname(__file__), "lint.py"))
lint = importlib.util.module_from_spec(spec); spec.loader.exec_module(lint)

def build(tmp):
    w = pathlib.Path(tmp); (w/"wiki/concepts").mkdir(parents=True)
    (w/"wiki/maps").mkdir(parents=True)
    # good concept: has frontmatter, a cited claim, links to hub
    (w/"wiki/concepts/good.md").write_text(
        "---\ntype: concept\n---\n# Good\n- X holds.^[from [[Hub]] — \"x\"]\n[[Hub]]\n", encoding="utf-8")
    # orphan: frontmatter ok, nothing links to it, links nowhere
    (w/"wiki/concepts/orphan.md").write_text(
        "---\ntype: concept\n---\n# Orphan\n", encoding="utf-8")
    # missing frontmatter
    (w/"wiki/concepts/nofm.md").write_text("# NoFM\n[[Good]]\n", encoding="utf-8")
    # unsourced claim bullet on a concept page
    (w/"wiki/concepts/unsourced.md").write_text(
        "---\ntype: concept\n---\n# U\n- A bare claim with no citation.\n[[Good]]\n", encoding="utf-8")
    # hub links to good + a broken target
    (w/"wiki/maps/Hub.md").write_text(
        "---\ntype: map\n---\n# Hub\n[[Good]] [[Nonexistent]]\n", encoding="utf-8")

with tempfile.TemporaryDirectory() as tmp:
    build(tmp)
    r = lint.lint(tmp)
    names = lambda k: {pathlib.Path(p).name for p,_ in r[k]}
    assert "Nonexistent" in {t for _,t in r["broken_links"]}, r["broken_links"]
    assert "orphan.md" in names("orphans"), r["orphans"]
    assert "nofm.md" in names("missing_frontmatter"), r["missing_frontmatter"]
    assert "unsourced.md" in names("unsourced_claims"), r["unsourced_claims"]
    # good.md must NOT be flagged anywhere
    for k in ("orphans","missing_frontmatter","unsourced_claims"):
        assert "good.md" not in names(k), (k, r[k])
    print("ALL LINT TESTS PASSED")


# --- C1 regression: CRLF files must not fool type detection ---

def test_crlf_ftype_detected():
    """_ftype must strip \\r so 'concept\\r' never leaks out (C1 fix)."""
    crlf_fm = b"---\r\ntype: concept\r\n---\r\n# Title\r\n"
    text = crlf_fm.decode("utf-8")
    assert lint._ftype(text) == "concept", f"got: {lint._ftype(text)!r}"


def test_crlf_unsourced_claim_reported():
    """On a CRLF concept page an unsourced claim bullet must be reported (C1 fix)."""
    with tempfile.TemporaryDirectory() as tmp:
        w = pathlib.Path(tmp)
        (w / "wiki" / "concepts").mkdir(parents=True)
        (w / "wiki" / "maps").mkdir(parents=True)
        # Write with explicit CRLF line endings
        (w / "wiki" / "concepts" / "crlf_concept.md").write_bytes(
            b"---\r\ntype: concept\r\n---\r\n# C\r\n- Unsourced claim here.\r\n"
        )
        # hub so other pages have inbound
        (w / "wiki" / "maps" / "Hub.md").write_text(
            "---\ntype: map\n---\n# Hub\n[[crlf_concept]]\n", encoding="utf-8"
        )
        r = lint.lint(tmp)
        unsourced_files = {pathlib.Path(p).name for p, _ in r["unsourced_claims"]}
        assert "crlf_concept.md" in unsourced_files, (
            f"CRLF concept page not detected; unsourced_claims={r['unsourced_claims']}"
        )


# --- C2 regression: orphan pass uses ftype_cache (no second read) ---

def test_orphan_pass_uses_cache(monkeypatch):
    """Ensure the orphan pass does not call p.read_text() a second time (C2 fix)."""
    read_calls = []
    original_read_text = pathlib.Path.read_text

    def counting_read_text(self, **kwargs):
        read_calls.append(self.name)
        return original_read_text(self, **kwargs)

    monkeypatch.setattr(pathlib.Path, "read_text", counting_read_text)

    with tempfile.TemporaryDirectory() as tmp:
        w = pathlib.Path(tmp)
        (w / "wiki" / "concepts").mkdir(parents=True)
        (w / "wiki" / "concepts" / "alpha.md").write_text(
            "---\ntype: concept\n---\n# Alpha\n", encoding="utf-8"
        )
        lint.lint(tmp)

    # Each file should be read exactly once: during the main loop.
    # If the orphan pass re-reads, "alpha.md" would appear twice.
    assert read_calls.count("alpha.md") == 1, (
        f"alpha.md was read {read_calls.count('alpha.md')} times; expected 1"
    )
