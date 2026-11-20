import time

import httpx
import pytest
from fastapi.testclient import TestClient

from app import agent_engine, github_fetcher
from app.main import app  # importing app loads backend/.env
from app.sample_data import get_sample_graph

client = TestClient(app)

PROVIDER_KEYS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY")
LIVE_PROVIDER = agent_engine.get_provider()  # evaluated once, before any test clears env vars


@pytest.fixture
def no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in PROVIDER_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def fake_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in PROVIDER_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-1234567890")


_REAL_ASYNC_CLIENT = httpx.AsyncClient


def _mock_github(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    transport = httpx.MockTransport(handler)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)  # never send (or log) a real token to the mock
    monkeypatch.setattr(
        github_fetcher.httpx, "AsyncClient", lambda **kw: _REAL_ASYNC_CLIENT(transport=transport, **kw)
    )


# ---------- /health ----------


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------- /api/analyze ----------


def test_analyze_sample_under_two_seconds() -> None:
    start = time.perf_counter()
    response = client.post("/api/analyze", json={"use_sample": True})
    elapsed = time.perf_counter() - start
    body = response.json()
    assert response.status_code == 200
    assert elapsed < 2.0
    assert body["source_type"] == "sample"
    assert len(body["nodes"]) > 0 and len(body["edges"]) > 0


def test_analyze_invalid_url_returns_400() -> None:
    response = client.post("/api/analyze", json={"repo_url": "not a github url"})
    assert response.status_code == 400
    assert "Invalid GitHub URL" in response.json()["detail"]


def test_analyze_empty_repo_returns_exact_message(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[{"type": "file", "path": "README.md", "name": "README.md", "size": 5, "download_url": "https://raw.test/README.md"}],
        )

    _mock_github(monkeypatch, handler)
    response = client.post("/api/analyze", json={"repo_url": "https://github.com/octocat/docs-only"})
    assert response.status_code == 400
    assert response.json()["detail"] == "No supported source files found (.py, .ts, .js). Try the sample project."


def test_analyze_respects_50_file_cap_and_depth_4(monkeypatch: pytest.MonkeyPatch) -> None:
    def entry(path: str, typ: str = "file") -> dict:
        return {
            "type": typ, "path": path, "name": path.split("/")[-1], "size": 10,
            "download_url": f"https://raw.test/{path}" if typ == "file" else None,
        }

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.startswith("https://raw.test/"):
            return httpx.Response(200, text="")
        path = url.split("/contents/")[1] if "/contents/" in url else ""
        depth = 0 if path == "" else path.count("/") + 1
        if depth >= 6:
            return httpx.Response(404, json={})
        nxt = f"{path}/d" if path else "d"
        listing = [entry(f"{path}/f.py" if path else "f.py"), entry(nxt, "dir")]
        return httpx.Response(200, json=listing)

    _mock_github(monkeypatch, handler)
    body = client.post("/api/analyze", json={"repo_url": "https://github.com/o/deep"}).json()
    paths = {n["path"] for n in body["nodes"]}
    # root is depth 0; directories up to depth 4 are listed => f.py at levels 0..4
    assert "d/d/d/d/f.py" in paths
    assert "d/d/d/d/d/f.py" not in paths

    def many(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.startswith("https://raw.test/"):
            return httpx.Response(200, text="")
        return httpx.Response(200, json=[entry(f"m{i}.py") for i in range(60)])

    _mock_github(monkeypatch, many)
    body = client.post("/api/analyze", json={"repo_url": "https://github.com/o/big"}).json()
    assert len(body["nodes"]) == 50
    assert body["truncated"] is True and body["truncation_notice"]


# ---------- /api/impact ----------


def test_impact_direct_and_transitive() -> None:
    response = client.post("/api/impact", json={"target_id": "backend/auth.py"})
    body = response.json()
    assert response.status_code == 200
    assert body["direct_impacts"] == ["backend/routes.py"]
    assert body["transitive_impacts"] == ["frontend/CheckoutView.tsx", "frontend/apiClient.ts"]


def test_impact_unknown_node_returns_404() -> None:
    response = client.post("/api/impact", json={"target_id": "does/not/exist.py"})
    assert response.status_code == 404


def test_impact_circular_dependency_is_flagged_and_terminates() -> None:
    nodes = [{"id": n, "label": n, "path": n} for n in ("a.py", "b.py", "c.py")]
    edges = [
        {"source": "a.py", "target": "b.py"},
        {"source": "b.py", "target": "a.py"},
        {"source": "c.py", "target": "a.py"},
    ]
    response = client.post("/api/impact", json={"target_id": "a.py", "nodes": nodes, "edges": edges})
    body = response.json()
    assert response.status_code == 200
    assert "circular dependency" in body["notes"].lower()
    assert sorted(body["direct_impacts"]) == ["b.py", "c.py"]
    assert body["transitive_impacts"] == []


def test_analyze_payload_reports_cycles() -> None:
    from app.parser import build_graph

    _, _, cycles = build_graph({"x.py": "import y", "y.py": "import x"})
    assert [c.nodes for c in cycles] == [["x.py", "y.py"]]


# ---------- /api/ask ----------


def test_ask_without_api_key_returns_banner(no_api_key: None) -> None:
    response = client.post("/api/ask", json={"question": "What breaks if backend/auth.py changes?"})
    body = response.json()
    assert response.status_code == 200
    assert body["answer"] == "AI Q&A unavailable — no API key configured."
    assert body["available"] is False


def test_ask_empty_graph_returns_fallback(fake_api_key: None, monkeypatch: pytest.MonkeyPatch) -> None:
    async def must_not_call(*args, **kwargs):  # pragma: no cover
        raise AssertionError("LLM must not be called for an empty graph")

    monkeypatch.setattr(agent_engine, "_call_llm", must_not_call)
    payload = {
        "question": "Anything?",
        "graph": {"source_type": "github", "repo_name": "o/empty", "nodes": [], "edges": []},
    }
    body = client.post("/api/ask", json=payload).json()
    assert body["answer"] == agent_engine.NO_GRAPH_MESSAGE
    assert body["available"] is True and body["referenced_nodes"] == []


def test_ask_without_graph_falls_back_to_sample(fake_api_key: None, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_llm(provider, system, user):
        assert "backend/auth.py" in user  # sample graph facts were supplied
        return "See `backend/auth.py`."

    monkeypatch.setattr(agent_engine, "_call_llm", fake_llm)
    body = client.post("/api/ask", json={"question": "What breaks if backend/auth.py changes?"}).json()
    assert body["referenced_nodes"] == ["backend/auth.py"]
    assert any("sample graph" in step for step in body["agent_trace"])


def test_ask_filters_hallucinated_paths(fake_api_key: None, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_llm(provider, system, user):
        if "Narrative" in system:
            return "Edit `backend/auth.py` and `backend/ghost.py`; `backend/routes.py` is affected."
        return "note"

    monkeypatch.setattr(agent_engine, "_call_llm", fake_llm)
    graph = get_sample_graph().model_dump()
    body = client.post(
        "/api/ask", json={"question": "Impact?", "graph": graph, "selected_node_id": "backend/auth.py"}
    ).json()
    assert body["referenced_nodes"] == ["backend/auth.py", "backend/routes.py"]
    assert "backend/ghost.py" not in body["referenced_nodes"]


def test_ask_llm_failure_returns_readable_error(fake_api_key: None, monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing(provider, system, user):
        raise agent_engine.LLMError("The AI provider timed out.")

    monkeypatch.setattr(agent_engine, "_call_llm", failing)
    response = client.post("/api/ask", json={"question": "Impact?", "graph": get_sample_graph().model_dump()})
    body = response.json()
    assert response.status_code == 200
    assert body["error"] == "The AI provider timed out."
    assert body["available"] is True


def test_ask_validates_question_length() -> None:
    assert client.post("/api/ask", json={"question": ""}).status_code == 422
    assert client.post("/api/ask", json={"question": "x" * 1001}).status_code == 422


@pytest.mark.live
@pytest.mark.skipif(LIVE_PROVIDER is None, reason="no LLM API key configured in env or backend/.env")
def test_ask_live_llm_is_grounded() -> None:
    response = client.post(
        "/api/ask",
        json={
            "question": "What breaks if backend/auth.py changes? Cite files.",
            "graph": get_sample_graph().model_dump(),
            "selected_node_id": "backend/auth.py",
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["error"] is None, body["error"]
    assert body["available"] is True
    assert len(body["answer"]) > 20
    assert body["answer"].rstrip()[-1] in ".!?)`*", f"answer looks truncated: ...{body['answer'][-60:]!r}"
    sample_ids = {n.id for n in get_sample_graph().nodes}
    assert body["referenced_nodes"], "live answer cited no files from the graph"
    assert set(body["referenced_nodes"]) <= sample_ids
