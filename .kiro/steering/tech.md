# Tech Stack & Conventions

## Repository Layout

- `backend/` — API, AST parsing, multi-agent orchestration.
- `frontend/` — web UI (diagram viewer + chat/voice console).
- `.kiro/` — steering, specs, hooks and settings (version-controlled).

## Backend

- Language: Python (type hints everywhere).
- API: REST/JSON; async request handling.
- Parsing: tree-sitter / language-specific AST parsers.
- Agents: orchestrator + specialised agents (architecture, dependency, narrative).

## Frontend

- Diagram rendering from the backend's parsed model (never re-parse in the browser).
- Chat panel streams responses from the backend.

## Conventions

- No secrets in the repository; configuration via `.env` (ignored by git).
- Keep `.kiro/` committed — do not add it to `.gitignore`.
- Small, focused commits with descriptive messages.
