from api_contract_studio.tester import is_destination_safe, redact_headers

def test_ssrf_rejects_localhost_by_default():
    safe, msg = is_destination_safe("http://localhost:8000")
    assert safe is False
    assert "reserved/loopback" in msg

def test_ssrf_rejects_127_0_0_1():
    safe, msg = is_destination_safe("http://127.0.0.1:3000")
    assert safe is False
    assert "reserved/loopback" in msg

def test_ssrf_rejects_metadata_service():
    safe, msg = is_destination_safe("http://169.254.169.254/latest/meta-data/")
    assert safe is False
    assert "restricted" in msg or "reserved" in msg

def test_ssrf_rejects_non_http():
    safe, msg = is_destination_safe("file:///etc/passwd")
    assert safe is False
    assert "Unsupported URL scheme" in msg

def test_ssrf_allows_local_when_flag_enabled():
    safe, _ = is_destination_safe("http://localhost:8000", allow_local=True)
    assert safe is True

def test_redact_sensitive_headers():
    raw_headers = {
        "Authorization": "Bearer secret-token-12345",
        "Content-Type": "application/json",
        "X-API-KEY": "topsecret-key",
        "Accept": "*/*"
    }
    redacted = redact_headers(raw_headers)
    assert redacted["Authorization"] == "[REDACTED]"
    assert redacted["X-API-KEY"] == "[REDACTED]"
    assert redacted["Content-Type"] == "application/json"
    assert redacted["Accept"] == "*/*"
