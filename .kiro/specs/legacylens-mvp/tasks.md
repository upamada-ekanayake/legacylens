# LegacyLens MVP Implementation Tasks

- [x] **Task 1: Project & Kiro Foundation**
  - Create public GitHub repo with MIT license and `.kiro/steering/` files.
  - Enable Kiro powers and verify `.kiro/` is tracked in Git.

- [ ] **Task 2: Spec Authoring & Refinement**
  - Finalize `requirements.md`, `design.md`, and `tasks.md` inside `.kiro/specs/legacylens-mvp/`.

- [ ] **Task 3: Backend Parser & Blast-Radius Engine (`backend/`)**
  - Set up FastAPI project structure and Pydantic models.
  - Implement AST/code parser (tree-sitter or ast module) with GitHub Contents API ingestion: cap 50 files, directory traversal depth 4, circular-import detection.
  - Implement directed dependency/impact calculator.
  - Bundle a pre-computed sample graph (Python + TypeScript multi-file project) as static JSON; expose it via the sample mode path.
  - Add **smoke-test assertions** (pytest, two tests only): (1) parser returns a non-empty graph for the bundled sample project; (2) blast-radius endpoint returns a non-empty impact list for a known node in the sample graph.

- [ ] **Task 4: Multi-Agent Reasoning & API Endpoints**
  - Implement `/api/analyze`, `/api/impact`, and `/api/ask` with grounded code context and graceful fallbacks.

- [ ] **Task 5: Frontend UI & Voice/Chat Experience (`frontend/`)**
  - Build Next.js workspace with graph visualization, blast-radius view, and chat/voice Q&A.
  - Connect frontend to backend APIs and verify end-to-end flow.

- [ ] **Task 6: Kiro Hooks, Polish, Demo & Submission**
  - Add `.kiro/hooks/` automation, run security/secret checks, deploy app, record <3 min YouTube demo, write Kiro write-up & bonus blog post, and submit on Devpost before deadline.