# CI/CD Integration Guide

API Contract Studio integrates into GitHub Actions, GitLab CI, and other CI/CD pipelines to block breaking changes before pull requests are merged.

## GitHub Actions Example

Create `.github/workflows/contract-diff.yml`:

```yaml
name: API Contract Diff Gate

on:
  pull_request:
    branches: [main]

jobs:
  check-api-contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install ACS CLI
        run: pip install api-contract-studio

      - name: Extract Baseline Contract from Base Branch
        env:
          BASE_REF: ${{ github.base_ref }}
        run: |
          git checkout "${BASE_REF:-main}" -- contracts/openapi.yaml
          cp contracts/openapi.yaml /tmp/baseline.yaml
          git checkout HEAD

      - name: Run Semantic Diff
        run: |
          acs diff /tmp/baseline.yaml contracts/openapi.yaml \
            --policy .api-contract-studio.yml \
            --format markdown \
            --out report.md

      - name: Post Job Summary
        if: always()
        run: cat report.md >> $GITHUB_STEP_SUMMARY
```

## Policy Configuration (`.api-contract-studio.yml`)

```yaml
version: 1

contracts:
  - name: core-api
    baseline: contracts/openapi.yaml
    candidate: contracts/candidate.yaml

policy:
  fail_on:
    - BREAKING
  potentially_breaking: warn
  severity_threshold: HIGH
  ignored_rules:
    - ACS-DOC-CHANGED

report:
  formats:
    - json
    - markdown
```
