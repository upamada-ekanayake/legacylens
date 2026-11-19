# LegacyLens MVP Requirements

## 1. Problem Overview
Developers onboarding onto unfamiliar or legacy repositories struggle to understand how modules connect, which files break when a change is made, and how architectural flows work end-to-end. LegacyLens combines code parsing, dependency/blast-radius analysis, multi-agent reasoning, interactive architecture diagrams, and chat/voice Q&A.

## 2. User Stories & Acceptance Criteria

### US-1: Repository / Codebase Ingestion
- **As a** developer, **I want to** provide a public GitHub repository URL (or load a built-in sample) **so that** I can analyze a codebase quickly and reliably.
- **Acceptance Criteria:**
  - Accepts a valid public GitHub repository URL and fetches supported source files (`.py`, `.ts`, `.js`) using the **GitHub Contents API** (no `git clone`). Caps ingestion at **50 source files**; if more exist, the first 50 (breadth-first) are used and a notice is shown.
  - Import/call traversal depth is capped at **3 levels** to prevent runaway graphs on large repos.
  - Returns a parsed graph within **10 seconds** for repos at or under 50 supported files.
  - A **"Load Sample"** button loads a bundled Python + TypeScript multi-file project. The backend returns a pre-computed graph without any network call, completing in **under 2 seconds**.
  - Rejects invalid, private, or unreachable URLs with a clear, actionable error message.
  - If the fetched repo contains **no supported source files**, displays: *"No supported source files found (.py, .ts, .js). Try the sample project."*

### US-2: Dependency Graph & Change Impact ("Blast Radius")
- **As a** developer, **I want to** inspect module/symbol relationships and see which components are affected if a specific file or symbol changes **so that** I can assess risk before editing code.
- **Acceptance Criteria:**
  - Builds a directed dependency graph of files, functions/classes, and imports/references.
  - Clicking a graph node sends `target_id` to `POST /api/impact`; the response renders within **3 seconds**, highlighting **direct dependents in orange** and **transitive dependents in yellow**.
  - Circular imports are handled without infinite loops; cycles are rendered with a **visual cycle indicator** (e.g. a dashed self-loop or badge on the node).
  - Clearly distinguishes observed code links from AI-inferred explanations.

### US-3: Interactive Architecture Diagram
- **As a** developer, **I want to** view an interactive visual diagram of the codebase architecture **so that** I can navigate components and trace execution paths visually.
- **Acceptance Criteria:**
  - Renders nodes and edges cleanly with node selection and impact highlighting.
  - Updates dynamically when a new codebase or target module is analyzed.

### US-4: Multi-Agent Codebase Q&A (Chat & Voice)
- **As a** developer, **I want to** ask architectural and impact questions via text chat or voice **so that** I get grounded answers referencing real files and symbols.
- **Acceptance Criteria:**
  - **Text chat is the primary path.** The Q&A panel is fully functional without any microphone or audio access.
  - Voice input uses the **browser Web Speech API** (no backend dependency); voice output uses **browser speech synthesis**. If the browser does not support either, the UI shows a "Voice unavailable" label — this is a non-failure state, not an error.
  - Answers cite specific file paths and symbols from the analyzed codebase.
  - If no LLM API key is configured, the Q&A panel displays a **persistent banner**: *"AI Q&A unavailable — no API key configured."* Graph analysis and blast-radius features remain fully functional in this state.
  - LLM errors or timeouts during a query return a user-readable error message; they do not crash the UI.

## 3. Non-Functional & Hackathon Constraints
- Must keep `.kiro/` committed in the public GitHub repository (never in `.gitignore`).
- Must avoid hardcoding secrets or API keys in source files or commits.
- Must run cleanly in local development and be deployable for live demo access.
- **Deployment targets:** FastAPI backend on **Railway or Render** (free tier, no Docker required for MVP); Next.js frontend on **Vercel**. Both must be verified live before the demo recording.