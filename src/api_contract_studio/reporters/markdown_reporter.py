from __future__ import annotations

from ..models import Compatibility, DiffReport, Severity


def format_markdown_report(report: DiffReport) -> str:
    """Generate a clean, readable Markdown report suitable for PR comments and CI summaries."""
    summary = report.summary
    status_badge = "✅ **PASSED**" if summary.passed_policy else "❌ **FAILED (Policy Violations Detected)**"

    lines = [
        f"# API Contract Comparison Report",
        "",
        f"**Status:** {status_badge}  ",
        f"**Baseline:** {report.baseline_title} (v{report.baseline_version})  ",
        f"**Candidate:** {report.candidate_title} (v{report.candidate_version})  ",
        f"**Timestamp:** {report.timestamp or 'N/A'}  ",
        "",
        "## Summary of Changes",
        "",
        "| Category | Count |",
        "| :--- | :---: |",
        f"| **Total Changes** | `{summary.total_changes}` |",
        f"| 🚨 **Breaking** | `{summary.breaking_count}` |",
        f"| ⚠️ **Potentially Breaking** | `{summary.potentially_breaking_count}` |",
        f"| 🟢 **Non-Breaking** | `{summary.non_breaking_count}` |",
        f"| ℹ️ **Informational** | `{summary.informational_count}` |",
        "",
        "### Severity Breakdown",
        "",
        f"- **Critical:** `{summary.critical_count}`",
        f"- **High:** `{summary.high_count}`",
        f"- **Medium:** `{summary.medium_count}`",
        f"- **Low:** `{summary.low_count}`",
        f"- **Info:** `{summary.info_count}`",
        "",
    ]

    if not report.findings:
        lines.append("No contract differences detected between baseline and candidate specifications.")
        return "\n".join(lines)

    lines.append("## Findings Detail")
    lines.append("")

    # Group by compatibility
    breaking = [f for f in report.findings if f.compatibility == Compatibility.BREAKING]
    pot_breaking = [f for f in report.findings if f.compatibility == Compatibility.POTENTIALLY_BREAKING]
    non_breaking = [f for f in report.findings if f.compatibility == Compatibility.NON_BREAKING]

    def _render_findings_table(items, title):
        if not items:
            return
        lines.append(f"### {title}")
        lines.append("")
        lines.append("| Rule ID | Severity | Location | Message | Remediation | Fails CI |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :---: |")
        for f in items:
            fails = "❌ Yes" if f.fails_ci else "No"
            lines.append(
                f"| `{f.rule_id}` | `{f.severity.value}` | `{f.location}` | {f.message} | {f.remediation} | {fails} |"
            )
        lines.append("")

    _render_findings_table(breaking, "🚨 Breaking Changes")
    _render_findings_table(pot_breaking, "⚠️ Potentially Breaking Changes")
    _render_findings_table(non_breaking, "🟢 Non-Breaking Changes")

    return "\n".join(lines)
