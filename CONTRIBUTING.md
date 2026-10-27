# Contributing to API Contract Studio

Thank you for your interest in contributing to API Contract Studio!

## Development Setup

1. **Prerequisites**:
   - Python 3.12+ (or `uv`)
   - Node.js 20+
   - Git

2. **Backend & CLI Setup**:
   ```bash
   uv venv --python 3.12 .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[api,dev]"
   uv pip install email-validator
   ```

3. **Frontend Setup**:
   ```bash
   cd apps/web
   npm install --ignore-scripts
   npm run dev
   ```

4. **Running Tests**:
   ```bash
   uv run pytest -v
   cd apps/web && npm run build
   ```

## Pull Request Guidelines

- All semantic comparison rules must include regression fixtures in `tests/engine/`.
- Ensure `pytest` passes with 0 failures before opening a pull request.
- Keep commits descriptive and atomic.
