#!/usr/bin/env python3
"""Deterministic community assignment for a node-link graph (no LLM)."""
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

def assign_communities(graph):
    G = nx.Graph()
    G.add_nodes_from(n["id"] for n in graph["nodes"])
    G.add_edges_from((l["source"], l["target"]) for l in graph["links"])
    if G.number_of_edges() == 0:
        communities = [{n} for n in G.nodes()]
    else:
        communities = [set(c) for c in greedy_modularity_communities(G)]
    # deterministic order: sort communities by their sorted node-id tuple
    communities.sort(key=lambda c: sorted(c))
    cid = {}
    for i, comm in enumerate(communities):
        for node_id in comm:
            cid[node_id] = i
    for n in graph["nodes"]:
        n["community"] = cid.get(n["id"], 0)
    return graph
