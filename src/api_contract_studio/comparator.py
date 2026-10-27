from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime, timezone

from .models import (
    ChangeCategory,
    Compatibility,
    DiffReport,
    DiffSummary,
    Finding,
    PolicyConfig,
    Severity,
)
from .parser import dereference_spec


def compare_specs(
    baseline_doc: Dict[str, Any],
    candidate_doc: Dict[str, Any],
    policy: Optional[PolicyConfig] = None,
) -> DiffReport:
    """Compare two OpenAPI documents semantically and produce a structured DiffReport."""
    if policy is None:
        policy = PolicyConfig()

    findings: List[Finding] = []

    # Safe dereference so references are resolved
    base = dereference_spec(baseline_doc)
    cand = dereference_spec(candidate_doc)

    base_info = base.get("info", {})
    cand_info = cand.get("info", {})
    base_title = base_info.get("title", "Baseline API")
    base_ver = str(base_info.get("version", "1.0.0"))
    cand_title = cand_info.get("title", "Candidate API")
    cand_ver = str(cand_info.get("version", "1.0.0"))

    # 1. Compare global security requirements
    _compare_global_security(base.get("security", []), cand.get("security", []), findings)

    # 2. Compare paths and operations
    base_paths = base.get("paths", {}) or {}
    cand_paths = cand.get("paths", {}) or {}

    all_path_keys = sorted(set(base_paths.keys()) | set(cand_paths.keys()))
    http_methods = ["get", "post", "put", "delete", "patch", "options", "head", "trace"]

    for path in all_path_keys:
        if path not in cand_paths:
            findings.append(Finding(
                rule_id="ACS-PATH-REMOVED",
                category=ChangeCategory.ENDPOINT,
                severity=Severity.CRITICAL,
                compatibility=Compatibility.BREAKING,
                location=f"#/paths/{path}",
                old_value=path,
                new_value=None,
                message=f"Path '{path}' was removed from the API.",
                remediation=f"Restore path '{path}' or deprecate it before removal.",
            ))
            continue

        if path not in base_paths:
            findings.append(Finding(
                rule_id="ACS-PATH-ADDED",
                category=ChangeCategory.ENDPOINT,
                severity=Severity.INFO,
                compatibility=Compatibility.NON_BREAKING,
                location=f"#/paths/{path}",
                old_value=None,
                new_value=path,
                message=f"New path '{path}' was added.",
                remediation="Document the new endpoint in consumer release notes.",
            ))
            continue

        base_item = base_paths[path] or {}
        cand_item = cand_paths[path] or {}

        # Path-level parameters
        base_path_params = {str(p["name"]): p for p in base_item.get("parameters", []) if isinstance(p, dict) and "name" in p}
        cand_path_params = {str(p["name"]): p for p in cand_item.get("parameters", []) if isinstance(p, dict) and "name" in p}

        for method in http_methods:
            base_op = base_item.get(method)
            cand_op = cand_item.get(method)

            if base_op and not cand_op:
                findings.append(Finding(
                    rule_id="ACS-METHOD-REMOVED",
                    category=ChangeCategory.ENDPOINT,
                    severity=Severity.CRITICAL,
                    compatibility=Compatibility.BREAKING,
                    location=f"#/paths/{path}/{method}",
                    old_value=method.upper(),
                    new_value=None,
                    message=f"HTTP method {method.upper()} on path '{path}' was removed.",
                    remediation=f"Keep {method.upper()} {path} supported or issue a migration window.",
                ))
            elif not base_op and cand_op:
                findings.append(Finding(
                    rule_id="ACS-METHOD-ADDED",
                    category=ChangeCategory.ENDPOINT,
                    severity=Severity.INFO,
                    compatibility=Compatibility.NON_BREAKING,
                    location=f"#/paths/{path}/{method}",
                    old_value=None,
                    new_value=method.upper(),
                    message=f"New HTTP method {method.upper()} added to path '{path}'.",
                    remediation="Ensure consumers know about the new method.",
                ))
            elif base_op and cand_op:
                op_loc = f"#/paths/{path}/{method}"
                _compare_operation(
                    path, method, base_op, cand_op, base_path_params, cand_path_params, op_loc, findings
                )

    # 3. Compare global components/schemas directly for changes
    _compare_components(base.get("components", {}), cand.get("components", {}), findings)

    # Evaluate against policy
    _apply_policy(findings, policy)

    summary = _calculate_summary(findings)
    return DiffReport(
        baseline_title=base_title,
        baseline_version=base_ver,
        candidate_title=cand_title,
        candidate_version=cand_ver,
        summary=summary,
        findings=findings,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _compare_operation(
    path: str,
    method: str,
    base_op: Dict[str, Any],
    cand_op: Dict[str, Any],
    base_path_params: Dict[str, Any],
    cand_path_params: Dict[str, Any],
    loc: str,
    findings: List[Finding],
) -> None:
    # 1. Compare operation parameters
    b_params = {str(p["name"]): p for p in base_op.get("parameters", []) if isinstance(p, dict) and "name" in p}
    c_params = {str(p["name"]): p for p in cand_op.get("parameters", []) if isinstance(p, dict) and "name" in p}

    # Combine with path-level parameters
    effective_b_params = {**base_path_params, **b_params}
    effective_c_params = {**cand_path_params, **c_params}

    for p_name, c_param in effective_c_params.items():
        if p_name not in effective_b_params:
            if c_param.get("required") is True:
                findings.append(Finding(
                    rule_id="ACS-REQ-PARAM-ADDED-REQUIRED",
                    category=ChangeCategory.REQUEST,
                    severity=Severity.HIGH,
                    compatibility=Compatibility.BREAKING,
                    location=f"{loc}/parameters/{p_name}",
                    old_value=None,
                    new_value=f"required=True, in={c_param.get('in')}",
                    message=f"New required parameter '{p_name}' added to {method.upper()} {path}.",
                    remediation=f"Make parameter '{p_name}' optional with a sensible default value.",
                ))
            else:
                findings.append(Finding(
                    rule_id="ACS-REQ-PARAM-ADDED-OPTIONAL",
                    category=ChangeCategory.REQUEST,
                    severity=Severity.LOW,
                    compatibility=Compatibility.NON_BREAKING,
                    location=f"{loc}/parameters/{p_name}",
                    old_value=None,
                    new_value=f"required=False, in={c_param.get('in')}",
                    message=f"Optional parameter '{p_name}' added to {method.upper()} {path}.",
                    remediation="Document the new optional parameter.",
                ))

    for p_name, b_param in effective_b_params.items():
        if p_name not in effective_c_params:
            is_req = b_param.get("required") is True
            findings.append(Finding(
                rule_id="ACS-REQ-PARAM-REMOVED",
                category=ChangeCategory.REQUEST,
                severity=Severity.HIGH if is_req else Severity.MEDIUM,
                compatibility=Compatibility.BREAKING if is_req else Compatibility.POTENTIALLY_BREAKING,
                location=f"{loc}/parameters/{p_name}",
                old_value=f"name={p_name}, in={b_param.get('in')}",
                new_value=None,
                message=f"Parameter '{p_name}' was removed from {method.upper()} {path}.",
                remediation=f"Retain '{p_name}' as an optional deprecated parameter.",
            ))
        else:
            c_param = effective_c_params[p_name]
            # Changed location?
            if b_param.get("in") != c_param.get("in"):
                findings.append(Finding(
                    rule_id="ACS-REQ-PARAM-LOCATION-CHANGED",
                    category=ChangeCategory.REQUEST,
                    severity=Severity.HIGH,
                    compatibility=Compatibility.BREAKING,
                    location=f"{loc}/parameters/{p_name}/in",
                    old_value=str(b_param.get("in")),
                    new_value=str(c_param.get("in")),
                    message=f"Parameter '{p_name}' location changed from '{b_param.get('in')}' to '{c_param.get('in')}'.",
                    remediation="Keep parameter in its original location or support both locations.",
                ))
            # Made required?
            if not b_param.get("required") and c_param.get("required"):
                findings.append(Finding(
                    rule_id="ACS-REQ-PARAM-REQUIRED-CHANGED",
                    category=ChangeCategory.REQUEST,
                    severity=Severity.HIGH,
                    compatibility=Compatibility.BREAKING,
                    location=f"{loc}/parameters/{p_name}/required",
                    old_value="required=False",
                    new_value="required=True",
                    message=f"Existing parameter '{p_name}' changed from optional to required.",
                    remediation="Keep the parameter optional.",
                ))
            # Schema type changed?
            b_schema = b_param.get("schema", {})
            c_schema = c_param.get("schema", {})
            if b_schema and c_schema:
                _compare_schemas(
                    b_schema, c_schema, f"{loc}/parameters/{p_name}/schema", is_request=True, findings=findings
                )

    # 2. Compare request body
    _compare_request_body(loc, base_op.get("requestBody"), cand_op.get("requestBody"), findings)

    # 3. Compare responses
    _compare_responses(loc, base_op.get("responses", {}), cand_op.get("responses", {}), findings)

    # 4. Compare operation security
    if "security" in cand_op or "security" in base_op:
        _compare_op_security(loc, base_op.get("security"), cand_op.get("security"), findings)


def _compare_request_body(
    loc: str,
    base_body: Optional[Dict[str, Any]],
    cand_body: Optional[Dict[str, Any]],
    findings: List[Finding],
) -> None:
    if not base_body and not cand_body:
        return

    req_loc = f"{loc}/requestBody"
    if not base_body and cand_body:
        is_req = cand_body.get("required", False)
        findings.append(Finding(
            rule_id="ACS-REQ-BODY-REQUIRED-ADDED" if is_req else "ACS-REQ-BODY-OPTIONAL-ADDED",
            category=ChangeCategory.REQUEST,
            severity=Severity.HIGH if is_req else Severity.LOW,
            compatibility=Compatibility.BREAKING if is_req else Compatibility.NON_BREAKING,
            location=req_loc,
            old_value=None,
            new_value=f"required={is_req}",
            message=f"A {'required' if is_req else 'optional'} request body was added.",
            remediation="Ensure existing clients without request body can still execute request.",
        ))
        return

    if base_body and not cand_body:
        findings.append(Finding(
            rule_id="ACS-REQ-BODY-REMOVED",
            category=ChangeCategory.REQUEST,
            severity=Severity.MEDIUM,
            compatibility=Compatibility.POTENTIALLY_BREAKING,
            location=req_loc,
            old_value="requestBody",
            new_value=None,
            message="Request body definition was removed.",
            remediation="Verify clients sending body payloads are not rejected.",
        ))
        return

    if base_body and cand_body:
        # Check required change
        if not base_body.get("required") and cand_body.get("required"):
            findings.append(Finding(
                rule_id="ACS-REQ-BODY-REQUIRED-CHANGED",
                category=ChangeCategory.REQUEST,
                severity=Severity.HIGH,
                compatibility=Compatibility.BREAKING,
                location=f"{req_loc}/required",
                old_value="required=False",
                new_value="required=True",
                message="Request body was changed from optional to required.",
                remediation="Keep request body optional or accept empty payloads.",
            ))

        base_content = base_body.get("content", {})
        cand_content = cand_body.get("content", {})

        for media_type, b_mt in base_content.items():
            if media_type not in cand_content:
                findings.append(Finding(
                    rule_id="ACS-REQ-MEDIA-TYPE-REMOVED",
                    category=ChangeCategory.REQUEST,
                    severity=Severity.HIGH,
                    compatibility=Compatibility.BREAKING,
                    location=f"{req_loc}/content/{media_type}",
                    old_value=media_type,
                    new_value=None,
                    message=f"Accepted request media type '{media_type}' was removed.",
                    remediation=f"Retain support for content-type '{media_type}'.",
                ))
            else:
                c_mt = cand_content[media_type]
                _compare_schemas(
                    b_mt.get("schema", {}),
                    c_mt.get("schema", {}),
                    f"{req_loc}/content/{media_type}/schema",
                    is_request=True,
                    findings=findings,
                )


def _compare_responses(
    loc: str,
    base_responses: Dict[str, Any],
    cand_responses: Dict[str, Any],
    findings: List[Finding],
) -> None:
    resps_loc = f"{loc}/responses"

    # Removed response codes
    for status_code, b_resp in base_responses.items():
        if status_code not in cand_responses:
            findings.append(Finding(
                rule_id="ACS-RESP-STATUS-REMOVED",
                category=ChangeCategory.RESPONSE,
                severity=Severity.HIGH,
                compatibility=Compatibility.BREAKING,
                location=f"{resps_loc}/{status_code}",
                old_value=str(status_code),
                new_value=None,
                message=f"Response status code '{status_code}' was removed.",
                remediation=f"Continue documenting and returning status code '{status_code}'.",
            ))
        else:
            c_resp = cand_responses[status_code]
            _compare_single_response(resps_loc, str(status_code), b_resp, c_resp, findings)

    # Added response codes
    for status_code in cand_responses.keys():
        if status_code not in base_responses:
            findings.append(Finding(
                rule_id="ACS-RESP-STATUS-ADDED",
                category=ChangeCategory.RESPONSE,
                severity=Severity.MEDIUM,
                compatibility=Compatibility.POTENTIALLY_BREAKING,
                location=f"{resps_loc}/{status_code}",
                old_value=None,
                new_value=str(status_code),
                message=f"New response status code '{status_code}' added.",
                remediation="Check if consumer error-handling handles new response code gracefully.",
            ))


def _compare_single_response(
    resps_loc: str,
    status_code: str,
    b_resp: Dict[str, Any],
    c_resp: Dict[str, Any],
    findings: List[Finding],
) -> None:
    resp_loc = f"{resps_loc}/{status_code}"
    b_content = b_resp.get("content", {}) if isinstance(b_resp, dict) else {}
    c_content = c_resp.get("content", {}) if isinstance(c_resp, dict) else {}

    for media_type, b_mt in b_content.items():
        if media_type not in c_content:
            findings.append(Finding(
                rule_id="ACS-RESP-MEDIA-TYPE-REMOVED",
                category=ChangeCategory.RESPONSE,
                severity=Severity.HIGH,
                compatibility=Compatibility.BREAKING,
                location=f"{resp_loc}/content/{media_type}",
                old_value=media_type,
                new_value=None,
                message=f"Response media type '{media_type}' was removed for status '{status_code}'.",
                remediation=f"Retain '{media_type}' responses for existing clients.",
            ))
        else:
            c_mt = c_content[media_type]
            _compare_schemas(
                b_mt.get("schema", {}),
                c_mt.get("schema", {}),
                f"{resp_loc}/content/{media_type}/schema",
                is_request=False,
                findings=findings,
            )


def _compare_schemas(
    b_schema: Dict[str, Any],
    c_schema: Dict[str, Any],
    loc: str,
    is_request: bool,
    findings: List[Finding],
) -> None:
    if not isinstance(b_schema, dict) or not isinstance(c_schema, dict):
        return

    b_type = b_schema.get("type")
    c_type = c_schema.get("type")

    # Type change
    if b_type and c_type and b_type != c_type:
        findings.append(Finding(
            rule_id="ACS-SCHEMA-TYPE-CHANGED",
            category=ChangeCategory.SCHEMA,
            severity=Severity.HIGH,
            compatibility=Compatibility.BREAKING,
            location=f"{loc}/type",
            old_value=str(b_type),
            new_value=str(c_type),
            message=f"Schema type changed from '{b_type}' to '{c_type}'.",
            remediation="Preserve original schema type or provide backward-compatible parsing.",
        ))
        return

    # Nullability change
    b_null = b_schema.get("nullable", False)
    c_null = c_schema.get("nullable", False)
    if b_null and not c_null:
        # In response: client might receive null? No, if response became non-nullable, client expecting null is ok.
        # But in request: client sending null will now fail!
        sev = Severity.HIGH if is_request else Severity.MEDIUM
        compat = Compatibility.BREAKING if is_request else Compatibility.POTENTIALLY_BREAKING
        findings.append(Finding(
            rule_id="ACS-SCHEMA-NULLABILITY-RESTRICTED",
            category=ChangeCategory.SCHEMA,
            severity=sev,
            compatibility=compat,
            location=f"{loc}/nullable",
            old_value="nullable=True",
            new_value="nullable=False",
            message="Schema became non-nullable (disallows null values).",
            remediation="Keep field nullable if clients may submit or expect null.",
        ))

    # Enum narrowing
    b_enum = b_schema.get("enum")
    c_enum = c_schema.get("enum")
    if isinstance(b_enum, list) and isinstance(c_enum, list):
        removed_enum = set(b_enum) - set(c_enum)
        added_enum = set(c_enum) - set(b_enum)

        if removed_enum:
            # Removing enum value:
            # In request: server no longer accepts value => BREAKING
            # In response: server no longer returns value => POTENTIALLY_BREAKING
            sev = Severity.HIGH if is_request else Severity.MEDIUM
            compat = Compatibility.BREAKING if is_request else Compatibility.POTENTIALLY_BREAKING
            findings.append(Finding(
                rule_id="ACS-SCHEMA-ENUM-REMOVED",
                category=ChangeCategory.SCHEMA,
                severity=sev,
                compatibility=compat,
                location=f"{loc}/enum",
                old_value=str(sorted(list(removed_enum))),
                new_value=None,
                message=f"Enum values removed: {sorted(list(removed_enum))}.",
                remediation="Retain previous enum values for backward compatibility.",
            ))

        if added_enum:
            # Adding enum value:
            # In request: safe (server accepts more) => NON_BREAKING
            # In response: unsafe if client enum parser fails on unknown values => POTENTIALLY_BREAKING
            sev = Severity.LOW if is_request else Severity.MEDIUM
            compat = Compatibility.NON_BREAKING if is_request else Compatibility.POTENTIALLY_BREAKING
            findings.append(Finding(
                rule_id="ACS-SCHEMA-ENUM-EXPANDED",
                category=ChangeCategory.SCHEMA,
                severity=sev,
                compatibility=compat,
                location=f"{loc}/enum",
                old_value=None,
                new_value=str(sorted(list(added_enum))),
                message=f"Enum values added: {sorted(list(added_enum))}.",
                remediation="Ensure client enum parsers tolerate new variants.",
            ))

    # Array items comparison
    if b_type == "array" or "items" in b_schema:
        b_items = b_schema.get("items", {})
        c_items = c_schema.get("items", {})
        if isinstance(b_items, dict) and isinstance(c_items, dict):
            _compare_schemas(b_items, c_items, f"{loc}/items", is_request=is_request, findings=findings)

    # Object properties comparison
    b_props = b_schema.get("properties", {}) or {}
    c_props = c_schema.get("properties", {}) or {}
    b_required = set(b_schema.get("required", []) or [])
    c_required = set(c_schema.get("required", []) or [])

    # Check removed properties
    for prop_name, b_prop in b_props.items():
        prop_loc = f"{loc}/properties/{prop_name}"
        if prop_name not in c_props:
            if is_request:
                # Removed request property is potentially breaking (or non-breaking if optional)
                findings.append(Finding(
                    rule_id="ACS-REQ-PROP-REMOVED",
                    category=ChangeCategory.SCHEMA,
                    severity=Severity.MEDIUM,
                    compatibility=Compatibility.POTENTIALLY_BREAKING,
                    location=prop_loc,
                    old_value=prop_name,
                    new_value=None,
                    message=f"Request property '{prop_name}' was removed.",
                    remediation=f"Retain property '{prop_name}' as optional/ignored.",
                ))
            else:
                # Removed response property is BREAKING for consumer reading that field!
                findings.append(Finding(
                    rule_id="ACS-RESP-PROP-REMOVED",
                    category=ChangeCategory.SCHEMA,
                    severity=Severity.HIGH,
                    compatibility=Compatibility.BREAKING,
                    location=prop_loc,
                    old_value=prop_name,
                    new_value=None,
                    message=f"Response property '{prop_name}' was removed.",
                    remediation=f"Retain response property '{prop_name}' to avoid breaking existing clients.",
                ))
        else:
            c_prop = c_props[prop_name]
            # Recursively check property schema
            _compare_schemas(b_prop, c_prop, prop_loc, is_request=is_request, findings=findings)

    # Check added properties
    for prop_name, c_prop in c_props.items():
        prop_loc = f"{loc}/properties/{prop_name}"
        if prop_name not in b_props:
            is_req_now = prop_name in c_required
            if is_request:
                if is_req_now:
                    findings.append(Finding(
                        rule_id="ACS-REQ-BODY-PROP-REQUIRED-ADDED",
                        category=ChangeCategory.SCHEMA,
                        severity=Severity.HIGH,
                        compatibility=Compatibility.BREAKING,
                        location=prop_loc,
                        old_value=None,
                        new_value=f"required=True",
                        message=f"Required request property '{prop_name}' was added.",
                        remediation=f"Make property '{prop_name}' optional with default.",
                    ))
                else:
                    findings.append(Finding(
                        rule_id="ACS-REQ-BODY-PROP-OPTIONAL-ADDED",
                        category=ChangeCategory.SCHEMA,
                        severity=Severity.LOW,
                        compatibility=Compatibility.NON_BREAKING,
                        location=prop_loc,
                        old_value=None,
                        new_value="required=False",
                        message=f"Optional request property '{prop_name}' was added.",
                        remediation="Document the new optional property.",
                    ))
            else:
                # Response property added
                findings.append(Finding(
                    rule_id="ACS-RESP-PROP-ADDED",
                    category=ChangeCategory.SCHEMA,
                    severity=Severity.LOW,
                    compatibility=Compatibility.NON_BREAKING,
                    location=prop_loc,
                    old_value=None,
                    new_value=prop_name,
                    message=f"Response property '{prop_name}' was added.",
                    remediation="Inform consumers of the new response property.",
                ))

    # Check newly required existing properties
    newly_required = c_required - b_required
    for req_prop in newly_required:
        if req_prop in b_props:
            if is_request:
                findings.append(Finding(
                    rule_id="ACS-REQ-PROP-BECAME-REQUIRED",
                    category=ChangeCategory.SCHEMA,
                    severity=Severity.HIGH,
                    compatibility=Compatibility.BREAKING,
                    location=f"{loc}/required/{req_prop}",
                    old_value="optional",
                    new_value="required",
                    message=f"Request property '{req_prop}' was previously optional and is now required.",
                    remediation=f"Keep property '{req_prop}' optional.",
                ))
            else:
                findings.append(Finding(
                    rule_id="ACS-RESP-PROP-BECAME-REQUIRED",
                    category=ChangeCategory.SCHEMA,
                    severity=Severity.MEDIUM,
                    compatibility=Compatibility.POTENTIALLY_BREAKING,
                    location=f"{loc}/required/{req_prop}",
                    old_value="optional",
                    new_value="required",
                    message=f"Response property '{req_prop}' is now marked as required.",
                    remediation="Verify server guarantees this field is always populated.",
                ))


def _compare_global_security(
    base_sec: List[Dict[str, Any]],
    cand_sec: List[Dict[str, Any]],
    findings: List[Finding],
) -> None:
    b_names = {list(s.keys())[0] for s in base_sec if isinstance(s, dict) and s}
    c_names = {list(s.keys())[0] for s in cand_sec if isinstance(s, dict) and s}

    removed = b_names - c_names
    added = c_names - b_names

    for sec in removed:
        findings.append(Finding(
            rule_id="ACS-SEC-SCHEME-REMOVED",
            category=ChangeCategory.SECURITY,
            severity=Severity.HIGH,
            compatibility=Compatibility.BREAKING,
            location=f"#/security/{sec}",
            old_value=sec,
            new_value=None,
            message=f"Global security requirement '{sec}' was removed.",
            remediation="Ensure client credentials using this scheme are still accepted.",
        ))

    for sec in added:
        findings.append(Finding(
            rule_id="ACS-SEC-SCHEME-ADDED",
            category=ChangeCategory.SECURITY,
            severity=Severity.HIGH,
            compatibility=Compatibility.BREAKING,
            location=f"#/security/{sec}",
            old_value=None,
            new_value=sec,
            message=f"New required global security scheme '{sec}' was added.",
            remediation="Make authentication optional or support legacy tokens during rollout.",
        ))


def _compare_op_security(
    loc: str,
    base_sec: Optional[List[Dict[str, Any]]],
    cand_sec: Optional[List[Dict[str, Any]]],
    findings: List[Finding],
) -> None:
    b_sec = base_sec or []
    c_sec = cand_sec or []

    b_names = {list(s.keys())[0] for s in b_sec if isinstance(s, dict) and s}
    c_names = {list(s.keys())[0] for s in c_sec if isinstance(s, dict) and s}

    if not b_names and c_names:
        findings.append(Finding(
            rule_id="ACS-SEC-OP-AUTH-ADDED",
            category=ChangeCategory.SECURITY,
            severity=Severity.CRITICAL,
            compatibility=Compatibility.BREAKING,
            location=f"{loc}/security",
            old_value="none",
            new_value=str(sorted(list(c_names))),
            message=f"Operation now requires authentication: {sorted(list(c_names))}.",
            remediation="Keep unauthenticated access or use deprecation notice.",
        ))


def _compare_components(
    b_components: Dict[str, Any],
    c_components: Dict[str, Any],
    findings: List[Finding],
) -> None:
    b_sec_schemes = (b_components or {}).get("securitySchemes", {}) or {}
    c_sec_schemes = (c_components or {}).get("securitySchemes", {}) or {}

    for name, b_scheme in b_sec_schemes.items():
        if name not in c_sec_schemes:
            findings.append(Finding(
                rule_id="ACS-SEC-SCHEME-DEF-REMOVED",
                category=ChangeCategory.SECURITY,
                severity=Severity.HIGH,
                compatibility=Compatibility.BREAKING,
                location=f"#/components/securitySchemes/{name}",
                old_value=name,
                new_value=None,
                message=f"Security scheme definition '{name}' was removed.",
                remediation=f"Retain security scheme '{name}'.",
            ))


def _apply_policy(findings: List[Finding], policy: PolicyConfig) -> None:
    for f in findings:
        if f.rule_id in policy.ignored_rules:
            f.fails_ci = False
            continue

        should_fail = False
        if f.compatibility in policy.fail_on:
            should_fail = True

        if f.compatibility == Compatibility.POTENTIALLY_BREAKING and policy.potentially_breaking == "fail":
            should_fail = True

        # Check severity threshold
        severity_order = {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }
        if severity_order.get(f.severity, 0) < severity_order.get(policy.severity_threshold, 3):
            # If below severity threshold, don't fail unless explicitly required
            if f.compatibility == Compatibility.BREAKING and Compatibility.BREAKING in policy.fail_on:
                pass  # Keep breaking as fail
            else:
                should_fail = False

        f.fails_ci = should_fail


def _calculate_summary(findings: List[Finding]) -> DiffSummary:
    summary = DiffSummary()
    summary.total_changes = len(findings)

    for f in findings:
        if f.compatibility == Compatibility.BREAKING:
            summary.breaking_count += 1
        elif f.compatibility == Compatibility.POTENTIALLY_BREAKING:
            summary.potentially_breaking_count += 1
        elif f.compatibility == Compatibility.NON_BREAKING:
            summary.non_breaking_count += 1
        elif f.compatibility == Compatibility.INFORMATIONAL:
            summary.informational_count += 1

        if f.severity == Severity.CRITICAL:
            summary.critical_count += 1
        elif f.severity == Severity.HIGH:
            summary.high_count += 1
        elif f.severity == Severity.MEDIUM:
            summary.medium_count += 1
        elif f.severity == Severity.LOW:
            summary.low_count += 1
        elif f.severity == Severity.INFO:
            summary.info_count += 1

    summary.passed_policy = not any(f.fails_ci for f in findings)
    return summary
