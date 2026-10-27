import subprocess
import sys

def test_cli_version():
    res = subprocess.run([sys.executable, "-m", "api_contract_studio.cli", "version"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "API Contract Studio CLI" in res.stdout

def test_cli_validate_success():
    res = subprocess.run(
        [sys.executable, "-m", "api_contract_studio.cli", "validate", "contracts/examples/baseline_petstore.yaml"],
        capture_output=True, text=True
    )
    assert res.returncode == 0
    assert "valid OpenAPI" in res.stdout

def test_cli_diff_breaking_returns_exit_1():
    res = subprocess.run(
        [
            sys.executable, "-m", "api_contract_studio.cli", "diff",
            "contracts/examples/baseline_petstore.yaml",
            "contracts/examples/candidate_breaking.yaml"
        ],
        capture_output=True, text=True
    )
    assert res.returncode == 1  # Policy violation exit code
    assert "FAILED" in res.stdout
    assert "ACS-PATH-REMOVED" in res.stdout

def test_cli_diff_non_breaking_returns_exit_0():
    res = subprocess.run(
        [
            sys.executable, "-m", "api_contract_studio.cli", "diff",
            "contracts/examples/baseline_petstore.yaml",
            "contracts/examples/candidate_non_breaking.yaml"
        ],
        capture_output=True, text=True
    )
    assert res.returncode == 0
    assert "PASSED" in res.stdout

def test_cli_diff_json_format():
    res = subprocess.run(
        [
            sys.executable, "-m", "api_contract_studio.cli", "diff",
            "contracts/examples/baseline_petstore.yaml",
            "contracts/examples/candidate_breaking.yaml",
            "--format", "json"
        ],
        capture_output=True, text=True
    )
    assert res.returncode == 1
    assert '"passed_policy": false' in res.stdout or '"passed_policy":false' in res.stdout

def test_cli_file_not_found_exit_2():
    res = subprocess.run(
        [sys.executable, "-m", "api_contract_studio.cli", "validate", "non_existent_file.yaml"],
        capture_output=True, text=True
    )
    assert res.returncode == 2
