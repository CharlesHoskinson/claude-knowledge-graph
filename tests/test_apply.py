# tests/test_apply.py
import subprocess
import pytest
import apply


def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def _init_repo(root):
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init")
    _git(root, "config", "user.name", "Test User")
    _git(root, "config", "user.email", "test@example.com")


def _tracked_files(root):
    out = _git(root, "ls-files")
    return set(l for l in out.stdout.splitlines() if l)


def test_fresh_dir_inits_repo_and_commits_only_wiki(tmp_path):
    # (a) fresh dir -> inits repo + commits only wiki files
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "page.md").write_text("hello", encoding="utf-8")
    apply.apply(str(wiki), "compile graphify wiki")
    assert _git(wiki, "rev-parse", "--is-inside-work-tree").stdout.strip() == "true"
    log = _git(wiki, "log", "--oneline")
    assert log.returncode == 0 and log.stdout.strip(), "expected a commit"
    assert _tracked_files(wiki) == {"page.md"}


def test_wiki_dir_that_is_repo_root_commits(tmp_path):
    # (b) wiki dir that is itself a repo root -> commits
    wiki = tmp_path / "wiki"
    _init_repo(wiki)
    (wiki / "page.md").write_text("hello", encoding="utf-8")
    apply.apply(str(wiki), "compile graphify wiki")
    log = _git(wiki, "log", "--oneline")
    assert log.returncode == 0 and log.stdout.strip()
    assert "page.md" in _tracked_files(wiki)


def test_nested_wiki_in_outer_repo_refuses_and_does_not_commit(tmp_path):
    # (c) wiki nested in an outer repo with an unrelated dirty file -> raises,
    # and the unrelated file is NOT committed.
    outer = tmp_path / "outer"
    _init_repo(outer)
    # an unrelated, untracked dirty file in the outer repo
    (outer / "unrelated.txt").write_text("do not stage me", encoding="utf-8")
    wiki = outer / "subdir" / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "page.md").write_text("hello", encoding="utf-8")

    with pytest.raises(RuntimeError) as exc:
        apply.apply(str(wiki), "compile graphify wiki")
    assert "nested" in str(exc.value).lower()

    # outer repo must have NO commit referencing the unrelated file (no commits at all)
    log = _git(outer, "log", "--oneline")
    assert not log.stdout.strip(), "outer repo should have no commits"
    # nothing was staged
    staged = _git(outer, "diff", "--cached", "--name-only")
    assert not staged.stdout.strip(), f"unexpected staged files: {staged.stdout!r}"
