# LegacyLens MVP Implementation Tasks

- [x] **Task 1: Project & Kiro Foundation**
  - Create public GitHub repo with MIT license and `.kiro/steering/` files.
  - Enable Kiro powers and verify `.kiro/` is tracked in Git.

- [ ] **Task 2: Spec Authoring & Refinement**
  - Finalize `requirements.md`, `design.md`, and `tasks.md` inside `.kiro/specs/legacylens-mvp/`.

- [ ] **Task 3: Backend Parser & Blast-Radius Engine (`backend/`)**
  - Set up FastAPI project structure and Pydantic models.
  - Implement AST/code parser and directed dependency/impact calculator + sample repo fallback.
  - Add unit tests for parsing and blast-radius calculations.

- [ ] **Task 4: Multi-Agent Reasoning & API Endpoints**
  - Implement `/api/analyze`, `/api/impact`, and `/api/ask` with grounded code context and graceful fallbacks.

- [ ] **Task 5: Frontend UI & Voice/Chat Experience (`frontend/`)**
  - Build Next.js workspace with graph visualization, blast-radius view, and chat/voice Q&A.
  - Connect frontend to backend APIs and verify end-to-end flow.

- [ ] **Task 6: Kiro Hooks, Polish, Demo & Submission**
  - Add `.kiro/hooks/` automation, run security/secret checks, deploy app, record <3 min YouTube demo, write Kiro write-up & bonus blog post, and submit on Devpost before deadline.