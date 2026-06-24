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
    _git(root, "add", "-A")
    _git(root, "commit", "-m", message)
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
