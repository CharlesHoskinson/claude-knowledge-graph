#!/usr/bin/env python3
"""Pluggable graph-generation backend interface."""
import subprocess

class GraphBackend:
    """Produce a node-link graph dict from a staged source + ontology.
    Implementations must write out_path and return the graph dict. `run` is an
    injectable subprocess.run-compatible callable so external tools can be faked in tests."""
    name = "base"

    def generate(self, manifest, ontology, out_path, run=subprocess.run):
        raise NotImplementedError
