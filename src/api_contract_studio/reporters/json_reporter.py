from __future__ import annotations

import json
from ..models import DiffReport


def format_json_report(report: DiffReport, indent: int = 2) -> str:
    """Format DiffReport as formatted JSON string matching schema."""
    return json.dumps(report.model_dump(), indent=indent)
