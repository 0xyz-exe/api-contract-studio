from __future__ import annotations

import ipaddress
import re
import socket
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse
import httpx
import jsonschema

from .models import TestResultItem, TestSuiteReport
from .parser import dereference_spec

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("10.0.0.0/8"),       # Private RFC 1918
    ipaddress.ip_network("172.16.0.0/12"),    # Private RFC 1918
    ipaddress.ip_network("192.168.0.0/16"),   # Private RFC 1918
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local / AWS / GCP / Azure metadata
    ipaddress.ip_network("100.64.0.0/10"),    # Carrier-grade NAT
    ipaddress.ip_network("0.0.0.0/8"),        # Broadcast/Current network
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),        # IPv6 link-local
]

SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key", "token", "session"}


class SSRFValidationError(Exception):
    """Raised when destination IP resolves to a restricted network range."""


def is_destination_safe(url: str, allow_local: bool = False) -> Tuple[bool, str]:
    """Validate destination URL against SSRF protection policies."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, f"Unsupported URL scheme: {parsed.scheme}. Only HTTP and HTTPS are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "Invalid URL: missing hostname."

    hostname_lower = hostname.lower()

    if not allow_local:
        if hostname_lower in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
            return False, f"Target '{hostname}' is a reserved/loopback destination."

        # Resolve DNS to examine actual IP addresses
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                for net in BLOCKED_IP_NETWORKS:
                    if ip_obj in net:
                        return False, f"Destination resolves to restricted address: {ip_str} in {net}"
        except socket.gaierror as e:
            return False, f"DNS resolution failed for hostname '{hostname}': {e}"

    return True, "Safe"


def redact_headers(headers: Dict[str, Any]) -> Dict[str, str]:
    """Redact sensitive headers such as Authorization, Cookie, API Keys."""
    redacted = {}
    for k, v in headers.items():
        if k.lower() in SENSITIVE_HEADERS:
            redacted[k] = "[REDACTED]"
        else:
            redacted[k] = str(v)
    return redacted


def run_contract_test(
    spec_doc: Dict[str, Any],
    base_url: str,
    allow_local: bool = False,
    allow_non_idempotent: bool = False,
    timeout_seconds: float = 10.0,
    headers: Optional[Dict[str, str]] = None,
) -> TestSuiteReport:
    """Execute live contract tests against target base_url matching spec_doc."""
    safe, reason = is_destination_safe(base_url, allow_local=allow_local)
    if not safe:
        raise SSRFValidationError(f"Target URL blocked by security policy: {reason}")

    doc = dereference_spec(spec_doc)
    paths = doc.get("paths", {}) or {}

    custom_headers = headers.copy() if headers else {}
    results: List[TestResultItem] = []
    start_all = time.time()

    base_url_clean = base_url.rstrip("/")

    # Safe HTTP methods to test without explicit non-idempotent permission
    safe_methods = {"get", "head", "options"}
    if allow_non_idempotent:
        safe_methods.update({"post", "put", "patch"})

    with httpx.Client(
        base_url=base_url_clean,
        timeout=timeout_seconds,
        follow_redirects=False,
    ) as client:
        for path_key, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method_str, op in path_item.items():
                method_lower = method_str.lower()
                if method_lower not in {"get", "post", "put", "delete", "patch", "options", "head"}:
                    continue

                if method_lower not in safe_methods:
                    # Skip unsafe/destructive or non-idempotent methods unless requested
                    continue

                # Don't invoke parameterized path endpoints blindly without configured values
                if "{" in path_key and "}" in path_key:
                    # Substitute simple dummy ID for testing simple /users/{id}
                    test_path = re.sub(r"\{[a-zA-Z0-9_]+\}", "1", path_key)
                else:
                    test_path = path_key

                expected_status = 200
                responses = op.get("responses", {})
                for sc in responses.keys():
                    if str(sc).isdigit():
                        expected_status = int(sc)
                        break

                t0 = time.time()
                error_msg = None
                observed_status = 0
                resp_headers_clean = {}

                try:
                    resp = client.request(method_lower.upper(), test_path, headers=custom_headers)
                    duration_ms = round((time.time() - t0) * 1000, 2)
                    observed_status = resp.status_code
                    resp_headers_clean = redact_headers(dict(resp.headers))

                    # Validate status code: check if observed status is among defined responses
                    status_str = str(observed_status)
                    passed = (status_str in responses) or (observed_status == expected_status) or ("default" in responses)
                    if not passed:
                        error_msg = f"Observed HTTP {observed_status}, expected one of {list(responses.keys())}"

                    # Validate response schema if JSON returned
                    if passed and "application/json" in resp.headers.get("content-type", ""):
                        sc_def = responses.get(status_str) or responses.get("default")
                        if isinstance(sc_def, dict):
                            content_def = sc_def.get("content", {}).get("application/json", {})
                            schema_def = content_def.get("schema")
                            if schema_def:
                                try:
                                    resp_json = resp.json()
                                    jsonschema.validate(instance=resp_json, schema=schema_def)
                                except jsonschema.ValidationError as ve:
                                    passed = False
                                    error_msg = f"Response schema validation error: {ve.message} at '{'.'.join(str(p) for p in ve.path)}'"
                                except Exception as exc:
                                    passed = False
                                    error_msg = f"Response body JSON parse error: {exc}"

                except Exception as exc:
                    duration_ms = round((time.time() - t0) * 1000, 2)
                    passed = False
                    error_msg = f"HTTP request failed: {exc}"

                results.append(TestResultItem(
                    endpoint=test_path,
                    method=method_lower.upper(),
                    expected_status=expected_status,
                    observed_status=observed_status,
                    passed=passed,
                    duration_ms=duration_ms,
                    error_message=error_msg,
                    details={"response_headers": resp_headers_clean},
                ))

    total_duration = round(time.time() - start_all, 3)
    passed_cnt = sum(1 for r in results if r.passed)
    failed_cnt = sum(1 for r in results if not r.passed)

    return TestSuiteReport(
        base_url=base_url_clean,
        total_tests=len(results),
        passed_tests=passed_cnt,
        failed_tests=failed_cnt,
        skipped_tests=0,
        duration_seconds=total_duration,
        results=results,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
