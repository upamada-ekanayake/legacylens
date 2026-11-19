# Project Structure

```text
legacylens/
├── .kiro/
│   ├── steering/          # product.md, tech.md, structure.md
│   ├── specs/             # feature specs
│   │   └── legacylens-mvp/
│   ├── hooks/             # Kiro hooks
│   └── settings/          # Kiro settings
├── backend/               # API, AST parsing, agent orchestration
├── frontend/              # web UI
├── LICENSE
└── README.md
```

## Rules

- `.kiro/` is part of the deliverable and must stay in version control.
- New features get a spec folder under `.kiro/specs/<feature-name>/`.
- Application code lives only in `backend/` or `frontend/`.
