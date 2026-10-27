# Command Line Interface (`acs`)

`api-contract-studio` ships with an installable command-line interface `acs`.

## Installation

```bash
pip install -e .
```

## Commands

### `acs version`
Displays current CLI version.

### `acs validate <spec_file>`
Validates an OpenAPI 3.0 or 3.1 specification for structural correctness and reference validity.
```bash
acs validate contracts/openapi.yaml
```

### `acs diff <baseline> <candidate> [options]`
Compares two OpenAPI specifications and evaluates breaking changes against configured policies.
```bash
acs diff baseline.yaml candidate.yaml \
  --policy .api-contract-studio.yml \
  --format markdown \
  --out pr-report.md
```

Options:
- `--policy <path>`: Custom YAML policy file.
- `--format table|json|markdown`: Output format (default: `table`).
- `--out <file>`: Write report directly to file.

### `acs test <spec_file> --base-url <url> [options]`
Executes live HTTP contract validation against running services.
```bash
acs test contracts/openapi.yaml --base-url http://localhost:8000 --allow-local
```

Options:
- `--base-url <url>`: Target HTTP/HTTPS endpoint.
- `--allow-local`: Authorize requests to `localhost` / `127.0.0.1` (blocked by default for SSRF safety).
- `--allow-non-idempotent`: Allow executing POST/PUT methods.

## Deterministic Exit Codes

| Code | Meaning |
| :---: | :--- |
| `0` | Success; no policy violations detected. |
| `1` | Policy violation detected (breaking change failing policy or test failure). |
| `2` | Invalid input or configuration error (file not found, syntax error). |
| `3` | Internal execution or network infrastructure error. |
