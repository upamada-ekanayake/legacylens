# LegacyLens Technical Design

## 1. High-Level Architecture
- **Frontend (`frontend/`):** Next.js (App Router) + TypeScript + Tailwind CSS
  - Codebase input bar (GitHub URL + sample codebase selector)
  - Interactive Dependency & Architecture Graph panel
  - Blast-Radius Inspector (selected node + impacted files/symbols)
  - Multi-Agent Q&A panel (text chat + voice input/playback)
- **Backend (`backend/`):** Python 3.11+ + FastAPI + Pydantic v2
  - `POST /api/analyze`: Ingests repo URL or sample codebase, runs parser + graph builder, returns normalized graph & summary
  - `POST /api/impact`: Computes blast radius for a selected file/symbol node
  - `POST /api/ask`: Runs multi-agent workflow (LangGraph / structured agent pipeline) over parsed context
- **Kiro Integration (`.kiro/`):**
  - `.kiro/steering/`: Product, technical, and repo structure rules
  - `.kiro/specs/`: Feature specs driving implementation and verification
  - `.kiro/hooks/`: Automated checks/workflows on file edits or pre-submit validation

## 2. Data Contracts (Core Schemas)
- `CodeNode`: `id`, `label`, `kind` (`file` | `module` | `symbol`), `path`, `summary`, `risk_level`
- `CodeEdge`: `source`, `target`, `relation` (`imports` | `calls` | `extends`)
- `ImpactReport`: `target_id`, `direct_impacts`, `transitive_impacts`, `risk_score`, `notes`
- `AskResponse`: `answer`, `referenced_nodes`, `agent_trace`

## 3. Error Handling & Demo Resilience
- Validate URLs and request payloads via Pydantic schemas (`400`/`422` for bad inputs).
- Include a bundled multi-file sample project in `backend/` so end-to-end analysis and impact tracing work offline or during rate limits.
- Return structured fallback responses rather than unhandled 500s when external services fail.