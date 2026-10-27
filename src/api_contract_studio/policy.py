from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import yaml

from .models import Compatibility, PolicyConfig, Severity


def load_policy_config(path: str | Path | None = None) -> PolicyConfig:
    """Load policy configuration from file (YAML/JSON) or return default."""
    if path is None:
        default_files = [".api-contract-studio.yml", ".api-contract-studio.yaml", "acs.yml"]
        for fname in default_files:
            p = Path(fname)
            if p.exists():
                path = p
                break

    if path is None:
        return PolicyConfig()

    p = Path(path)
    if not p.exists():
        return PolicyConfig()

    try:
        content = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        policy_dict = content.get("policy", content)

        fail_on_raw = policy_dict.get("fail_on", ["BREAKING"])
        fail_on = [Compatibility(x.upper()) for x in fail_on_raw if x.upper() in Compatibility.__members__]

        pot_breaking = str(policy_dict.get("potentially_breaking", "warn")).lower()
        sev_thresh_str = str(policy_dict.get("severity_threshold", "HIGH")).upper()
        sev_thresh = Severity[sev_thresh_str] if sev_thresh_str in Severity.__members__ else Severity.HIGH

        return PolicyConfig(
            fail_on=fail_on or [Compatibility.BREAKING],
            potentially_breaking=pot_breaking,
            severity_threshold=sev_thresh,
            allowed_rules=policy_dict.get("allowed_rules", []),
            ignored_rules=policy_dict.get("ignored_rules", []),
        )
    except Exception:
        # Fallback to standard policy on config load error
        return PolicyConfig()
