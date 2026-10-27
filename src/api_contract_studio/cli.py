from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .comparator import compare_specs
from .models import Compatibility, Severity
from .parser import SpecParseError, load_spec_file
from .policy import load_policy_config
from .reporters.json_reporter import format_json_report
from .reporters.markdown_reporter import format_markdown_report
from .tester import SSRFValidationError, run_contract_test
from .validator import validate_openapi_spec

# Exit codes per specification:
EXIT_SUCCESS = 0
EXIT_POLICY_VIOLATION = 1
EXIT_INVALID_INPUT = 2
EXIT_EXECUTION_ERROR = 3


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="acs",
        description="API Contract Studio CLI - Open-Source API Contract Testing & Breaking Change Detection",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: version
    subparsers.add_parser("version", help="Show API Contract Studio version")

    # Command: validate
    validate_p = subparsers.add_parser("validate", help="Validate an OpenAPI specification")
    validate_p.add_argument("spec", help="Path to OpenAPI YAML/JSON file")
    validate_p.add_argument("--format", choices=["table", "json"], default="table", help="Output format")

    # Command: diff
    diff_p = subparsers.add_parser("diff", help="Compare two OpenAPI specifications and detect breaking changes")
    diff_p.add_argument("baseline", help="Path to baseline specification")
    diff_p.add_argument("candidate", help="Path to candidate specification")
    diff_p.add_argument("--policy", help="Path to custom policy config file (.api-contract-studio.yml)")
    diff_p.add_argument("--format", choices=["table", "json", "markdown"], default="table", help="Report format")
    diff_p.add_argument("--out", help="Write report to output file")

    # Command: test
    test_p = subparsers.add_parser("test", help="Execute contract tests against a running API")
    test_p.add_argument("spec", help="Path to OpenAPI specification")
    test_p.add_argument("--base-url", required=True, help="Base URL of target API")
    test_p.add_argument("--allow-local", action="store_true", help="Allow testing localhost/private IPs (local dev only)")
    test_p.add_argument("--allow-non-idempotent", action="store_true", help="Allow testing POST/PUT/PATCH methods")
    test_p.add_argument("--format", choices=["table", "json"], default="table", help="Output format")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(EXIT_SUCCESS)

    if args.command == "version":
        print(f"API Contract Studio CLI v{__version__}")
        sys.exit(EXIT_SUCCESS)

    elif args.command == "validate":
        sys.exit(run_validate(args))

    elif args.command == "diff":
        sys.exit(run_diff(args))

    elif args.command == "test":
        sys.exit(run_test(args))

    sys.exit(EXIT_SUCCESS)


def run_validate(args) -> int:
    try:
        doc = load_spec_file(args.spec)
    except FileNotFoundError as e:
        sys.stderr.write(f"Error: {e}\n")
        return EXIT_INVALID_INPUT
    except SpecParseError as e:
        sys.stderr.write(f"Parse Error: {e}\n")
        return EXIT_INVALID_INPUT
    except Exception as e:
        sys.stderr.write(f"Execution Error: {e}\n")
        return EXIT_EXECUTION_ERROR

    res = validate_openapi_spec(doc)
    if args.format == "json":
        print(json.dumps(res.model_dump(), indent=2))
    else:
        if res.is_valid:
            print(f"✅ Specification is valid OpenAPI {res.openapi_version} ('{res.title}' v{res.version})")
        else:
            print(f"❌ Specification has validation errors:")
            for issue in res.issues:
                print(f"  [{issue.severity.value}] {issue.location}: {issue.message}")

    return EXIT_SUCCESS if res.is_valid else EXIT_POLICY_VIOLATION


def run_diff(args) -> int:
    try:
        base_doc = load_spec_file(args.baseline)
    except Exception as e:
        sys.stderr.write(f"Error loading baseline '{args.baseline}': {e}\n")
        return EXIT_INVALID_INPUT

    try:
        cand_doc = load_spec_file(args.candidate)
    except Exception as e:
        sys.stderr.write(f"Error loading candidate '{args.candidate}': {e}\n")
        return EXIT_INVALID_INPUT

    policy = load_policy_config(args.policy)
    report = compare_specs(base_doc, cand_doc, policy=policy)

    if args.format == "json":
        output = format_json_report(report)
    elif args.format == "markdown":
        output = format_markdown_report(report)
    else:
        # Table format
        summary = report.summary
        status = "PASSED" if summary.passed_policy else "FAILED"
        lines = [
            f"API Contract Studio Diff: {status}",
            f"Baseline:  {report.baseline_title} ({report.baseline_version})",
            f"Candidate: {report.candidate_title} ({report.candidate_version})",
            "",
            f"Changes:   Total={summary.total_changes} | Breaking={summary.breaking_count} | Potentially Breaking={summary.potentially_breaking_count} | Non-Breaking={summary.non_breaking_count}",
            f"Severity:  Critical={summary.critical_count} | High={summary.high_count} | Medium={summary.medium_count} | Low={summary.low_count}",
            "",
        ]
        if report.findings:
            lines.append("Findings:")
            for f in report.findings:
                symbol = "🚨" if f.compatibility == Compatibility.BREAKING else ("⚠️" if f.compatibility == Compatibility.POTENTIALLY_BREAKING else "🟢")
                fail_badge = " [FAILS CI]" if f.fails_ci else ""
                lines.append(f"  {symbol} [{f.severity.value}] {f.rule_id} at {f.location}{fail_badge}")
                lines.append(f"     Message:     {f.message}")
                lines.append(f"     Remediation: {f.remediation}")
        output = "\n".join(lines)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Report written to {args.out}")
    else:
        print(output)

    return EXIT_SUCCESS if report.summary.passed_policy else EXIT_POLICY_VIOLATION


def run_test(args) -> int:
    try:
        doc = load_spec_file(args.spec)
    except Exception as e:
        sys.stderr.write(f"Error loading specification '{args.spec}': {e}\n")
        return EXIT_INVALID_INPUT

    try:
        report = run_contract_test(
            doc,
            base_url=args.base_url,
            allow_local=args.allow_local,
            allow_non_idempotent=args.allow_non_idempotent,
        )
    except SSRFValidationError as e:
        sys.stderr.write(f"SSRF Security Violation: {e}\n")
        return EXIT_POLICY_VIOLATION
    except Exception as e:
        sys.stderr.write(f"Execution Error: {e}\n")
        return EXIT_EXECUTION_ERROR

    if args.format == "json":
        print(json.dumps(report.model_dump(), indent=2))
    else:
        print(f"Contract Test Results for {report.base_url}")
        print(f"Total: {report.total_tests} | Passed: {report.passed_tests} | Failed: {report.failed_tests} (took {report.duration_seconds}s)")
        for item in report.results:
            icon = "✅" if item.passed else "❌"
            print(f"  {icon} {item.method} {item.endpoint} -> Observed: {item.observed_status} (Expected: {item.expected_status}) in {item.duration_ms}ms")
            if item.error_message:
                print(f"     Error: {item.error_message}")

    return EXIT_SUCCESS if report.failed_tests == 0 else EXIT_POLICY_VIOLATION


if __name__ == "__main__":
    main()
