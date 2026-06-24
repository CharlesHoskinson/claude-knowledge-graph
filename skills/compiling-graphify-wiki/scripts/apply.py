#!/usr/bin/env python3
"""Commit a validated compiled wiki into its own git repo."""
import argparse, subprocess, sys, pathlib

def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)

def apply(wiki_root, message):
    root = pathlib.Path(wiki_root)
    if _git(root, "rev-parse", "--is-inside-work-tree").returncode != 0:
        _git(root, "init")
        _git(root, "config", "user.name", "Charles Hoskinson")
        _git(root, "config", "user.email", "Charles.Hoskinson@gmail.com")
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
