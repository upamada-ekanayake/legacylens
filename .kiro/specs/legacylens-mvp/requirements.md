# LegacyLens MVP Requirements

## 1. Problem Overview
Developers onboarding onto unfamiliar or legacy repositories struggle to understand how modules connect, which files break when a change is made, and how architectural flows work end-to-end. LegacyLens combines code parsing, dependency/blast-radius analysis, multi-agent reasoning, interactive architecture diagrams, and chat/voice Q&A.

## 2. User Stories & Acceptance Criteria

### US-1: Repository / Codebase Ingestion
- **As a** developer, **I want to** provide a public GitHub repository URL (or load a built-in sample/pasted snippet fallback) **so that** I can analyze a codebase quickly and reliably.
- **Acceptance Criteria:**
  - Accepts a valid public GitHub repository URL and fetches/parses supported source files (Python, TypeScript/JavaScript).
  - Provides a deterministic sample/fallback mode so live demos never fail due to network or GitHub rate limits.
  - Rejects invalid or private/unreachable inputs with clear, actionable error messages.

### US-2: Dependency Graph & Change Impact ("Blast Radius")
- **As a** developer, **I want to** inspect module/symbol relationships and see which components are affected if a specific file or symbol changes **so that** I can assess risk before editing code.
- **Acceptance Criteria:**
  - Builds a directed dependency graph of files, functions/classes, and imports/references.
  - Highlights direct and transitive dependents ("blast radius") when a node is selected.
  - Clearly distinguishes observed code links from AI-inferred explanations.

### US-3: Interactive Architecture Diagram
- **As a** developer, **I want to** view an interactive visual diagram of the codebase architecture **so that** I can navigate components and trace execution paths visually.
- **Acceptance Criteria:**
  - Renders nodes and edges cleanly with node selection and impact highlighting.
  - Updates dynamically when a new codebase or target module is analyzed.

### US-4: Multi-Agent Codebase Q&A (Chat & Voice)
- **As a** developer, **I want to** ask architectural and impact questions via text chat or voice **so that** I get grounded answers referencing real files and symbols.
- **Acceptance Criteria:**
  - Supports text prompts and browser/voice input/output (with graceful text fallback if microphone/audio is unavailable).
  - Cites specific file paths and symbols from the analyzed codebase.
  - Gracefully handles missing API keys or LLM errors with clear status feedback.

## 3. Non-Functional & Hackathon Constraints
- Must keep `.kiro/` committed in the public GitHub repository (never in `.gitignore`).
- Must avoid hardcoding secrets or API keys in source files or commits.
- Must run cleanly in local development and be deployable for live demo access.