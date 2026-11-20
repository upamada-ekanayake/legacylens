from typing import Literal, Optional

from pydantic import BaseModel, Field


class CodeNode(BaseModel):
    id: str
    label: str
    kind: Literal["file", "module", "symbol"] = "file"
    path: str
    summary: str = ""
    risk_level: Literal["low", "medium", "high"] = "low"


class CodeEdge(BaseModel):
    source: str
    target: str
    relation: Literal["imports", "calls", "extends"] = "imports"


class CycleInfo(BaseModel):
    nodes: list[str]
    description: str


class GraphPayload(BaseModel):
    source_type: Literal["sample", "github"]
    repo_name: str
    truncated: bool = False
    truncation_notice: Optional[str] = None
    nodes: list[CodeNode]
    edges: list[CodeEdge]
    cycles: list[CycleInfo] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    repo_url: Optional[str] = None
    use_sample: bool = False


class ImpactRequest(BaseModel):
    target_id: str
    nodes: list[CodeNode] = Field(default_factory=list)
    edges: list[CodeEdge] = Field(default_factory=list)


class ImpactReport(BaseModel):
    target_id: str
    direct_impacts: list[str] = Field(default_factory=list)
    transitive_impacts: list[str] = Field(default_factory=list)
    risk_score: int = 0
    notes: str = ""


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    graph: Optional[GraphPayload] = None
    selected_node_id: Optional[str] = None
    impact_report: Optional[ImpactReport] = None


class AskResponse(BaseModel):
    answer: str
    referenced_nodes: list[str] = Field(default_factory=list)
    agent_trace: Optional[list[str]] = None
    available: bool = True  # False only when no LLM API key is configured
    error: Optional[str] = None  # set when the LLM call failed; answer then holds a readable message
