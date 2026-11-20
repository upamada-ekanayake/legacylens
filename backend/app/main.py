import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .github_fetcher import FetchError, fetch_github_graph
from .graph_engine import compute_blast_radius
from .models import AnalyzeRequest, GraphPayload, ImpactReport, ImpactRequest
from .sample_data import get_sample_graph

load_dotenv()

app = FastAPI(title="LegacyLens API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=GraphPayload)
async def analyze_codebase(payload: AnalyzeRequest) -> GraphPayload:
    if payload.use_sample or not payload.repo_url:
        return get_sample_graph()

    try:
        return await fetch_github_graph(payload.repo_url, max_files=50, max_depth=3)
    except FetchError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/impact", response_model=ImpactReport)
async def analyze_impact(payload: ImpactRequest) -> ImpactReport:
    nodes = payload.nodes
    edges = payload.edges
    if not nodes:
        sample = get_sample_graph()
        nodes = sample.nodes
        edges = sample.edges

    try:
        return compute_blast_radius(target_id=payload.target_id, nodes=nodes, edges=edges)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown target_id: {payload.target_id}") from exc
