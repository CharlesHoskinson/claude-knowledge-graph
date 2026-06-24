# tests/test_gen_cluster.py
import cluster

def _graph():
    # two clusters: {a,b} connected, {c,d} connected, no cross edge
    return {"nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}],
            "links": [{"source": "a", "target": "b", "relation": "r"},
                      {"source": "c", "target": "d", "relation": "r"}]}

def test_every_node_gets_integer_community():
    g = cluster.assign_communities(_graph())
    assert all(isinstance(n["community"], int) for n in g["nodes"])

def test_connected_nodes_share_community_and_clusters_differ():
    g = cluster.assign_communities(_graph())
    comm = {n["id"]: n["community"] for n in g["nodes"]}
    assert comm["a"] == comm["b"]
    assert comm["c"] == comm["d"]
    assert comm["a"] != comm["c"]

def test_edgeless_graph_each_node_own_community_deterministic():
    g = cluster.assign_communities({"nodes": [{"id": "x"}, {"id": "y"}], "links": []})
    comms = sorted(n["community"] for n in g["nodes"])
    assert comms == [0, 1]
    again = cluster.assign_communities({"nodes": [{"id": "x"}, {"id": "y"}], "links": []})
    assert {n["id"]: n["community"] for n in again["nodes"]} == {"x": 0, "y": 1}
