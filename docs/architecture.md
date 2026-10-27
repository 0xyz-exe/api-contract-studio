# System Architecture

API Contract Studio is organized into decoupled layers:

```
┌────────────────────────────────────────────────────────┐
│                   Web UI (Next.js 16)                  │
│       Dashboard • Visual Diff • Testing • Reports      │
└───────────────────────────┬────────────────────────────┘
                            │ REST API (JSON)
┌───────────────────────────▼────────────────────────────┐
│                  Backend (FastAPI)                     │
│  Projects • Contracts • Revisions • SQLite / Postgres  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│             Core Engine (Python Package)               │
│ Parser • Validator • Comparator • Policy • HTTP Tester │
└───────────────────────────▲────────────────────────────┘
                            │
┌───────────────────────────┴────────────────────────────┐
│                    CLI (`acs`)                         │
│  acs validate • acs diff • acs test • CI Exit Codes    │
└────────────────────────────────────────────────────────┘
```

## Key Components

1. **Core Semantic Engine (`src/api_contract_studio`)**:
   - Zero dependence on database or web frameworks.
   - Deterministic semantic OpenAPI comparisons.
   - Safe local reference dereferencing with recursion cycle protection.

2. **Command Line Interface (`acs`)**:
   - Standalone CLI for local pre-commit and CI/CD pipelines.
   - Deterministic exit codes: `0` (clean), `1` (policy violation), `2` (invalid input), `3` (execution error).

3. **Backend Service (`apps/api`)**:
   - SQLAlchemy 2.x ORM models with SQLite default (PostgreSQL production-ready).
   - Alembic database migration management.
   - JWT authentication and project-level multi-tenant isolation.
   - Strict SSRF network protections.

4. **Web Frontend (`apps/web`)**:
   - Next.js 16 App Router with React 19, TypeScript strict mode, and Tailwind CSS.
   - Interactive Visual Diff explorer with real-time filters and JSON Pointer inspector.
