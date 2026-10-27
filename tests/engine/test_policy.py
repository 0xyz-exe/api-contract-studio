import textwrap
from api_contract_studio.policy import load_policy_config
from api_contract_studio.models import Compatibility, Severity

def test_load_default_policy():
    policy = load_policy_config(None)
    assert Compatibility.BREAKING in policy.fail_on
    assert policy.potentially_breaking == "warn"
    assert policy.severity_threshold == Severity.HIGH

def test_load_custom_policy(tmp_path):
    policy_file = tmp_path / "custom_policy.yml"
    policy_file.write_text(textwrap.dedent("""
    policy:
      fail_on:
        - BREAKING
        - POTENTIALLY_BREAKING
      potentially_breaking: fail
      severity_threshold: MEDIUM
      ignored_rules:
        - ACS-DOC-CHANGED
    """), encoding="utf-8")

    cfg = load_policy_config(policy_file)
    assert Compatibility.POTENTIALLY_BREAKING in cfg.fail_on
    assert cfg.potentially_breaking == "fail"
    assert cfg.severity_threshold == Severity.MEDIUM
    assert "ACS-DOC-CHANGED" in cfg.ignored_rules
