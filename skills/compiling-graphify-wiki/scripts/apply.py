#!/usr/bin/env python3
"""Commit a validated compiled wiki into its own git repo."""
import argparse, subprocess, sys, pathlib

def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)

def apply(wiki_root, message):
    root = pathlib.Path(wiki_root)
    inside = _git(root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        # Not inside any git repo: create a standalone wiki repo (unchanged path).
        _git(root, "init")
        _git(root, "config", "user.name", "Charles Hoskinson")
        _git(root, "config", "user.email", "Charles.Hoskinson@gmail.com")
    else:
        # Already inside a repo. Only auto-commit when the wiki IS that repo's
        # root; refuse if it is merely nested inside a LARGER repo, otherwise
        # `git add -A` would stage the entire outer worktree (unrelated changes)
        # and commit them under the wiki message.
        top = _git(root, "rev-parse", "--show-toplevel")
        toplevel = pathlib.Path(top.stdout.strip()).resolve() if top.returncode == 0 else None
        if toplevel is not None and toplevel != root.resolve():
            raise RuntimeError(
                f"Refusing to auto-commit: wiki '{root}' is nested inside the larger "
                f"git repo '{toplevel}'. A 'git add -A' here would stage unrelated "
                f"changes in that repo. Commit the wiki via that repo, or pass a "
                f"standalone wiki path."
            )
    add_result = _git(root, "add", "-A")
    if add_result.returncode != 0:
        raise RuntimeError(
            f"git add failed (exit {add_result.returncode})\n"
            f"stdout: {add_result.stdout}\nstderr: {add_result.stderr}"
        )
    commit_result = _git(root, "commit", "-m", message)
    if commit_result.returncode != 0:
        raise RuntimeError(
            f"git commit failed (exit {commit_result.returncode})\n"
            f"stdout: {commit_result.stdout}\nstderr: {commit_result.stderr}"
        )
    return None

def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki", required=True)
    ap.add_argument("--message", default="compile graphify wiki")
    a = ap.parse_args(argv)
    apply(a.wiki, a.message)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
