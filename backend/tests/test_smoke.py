from app.graph_engine import compute_blast_radius
from app.sample_data import get_sample_graph


def test_smoke_sample_graph_non_empty() -> None:
    graph = get_sample_graph()
    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0


def test_smoke_blast_radius_for_known_node() -> None:
    graph = get_sample_graph()
    report = compute_blast_radius(
        target_id="backend/auth.py",
        nodes=graph.nodes,
        edges=graph.edges,
    )
    assert len(report.direct_impacts) > 0
