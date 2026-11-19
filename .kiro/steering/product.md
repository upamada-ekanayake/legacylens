# LegacyLens Product Steering

## Vision
LegacyLens is a developer codebase archaeologist for the Kiroween 2026 Frankenstein category. It analyzes repositories/codebases, maps module dependencies and bug blast radii, generates interactive architecture diagrams, and answers developer questions via chat and voice.

## MVP Scope
- Accept a public GitHub repo URL (or sample/pasted code files for fast reliable demos).
- Parse code structure, imports/calls, and dependency graph.
- Compute change impact ("blast radius") when a target file/symbol changes.
- Render an interactive architecture graph + natural language / voice Q&A.

## Quality Bar
- Prioritize deterministic reliability and fast response times for demo flows.
- Never fabricate symbol names, file paths, or call relationships not present in parsed code.