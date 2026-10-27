from __future__ import annotations

import re
from typing import Any, Dict, List
from .models import Severity, ValidationIssue, ValidationResult
from .parser import SpecRefError, resolve_local_ref

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head", "trace"}
VALID_PARAM_IN = {"path", "query", "header", "cookie"}


def validate_openapi_spec(doc: Dict[str, Any]) -> ValidationResult:
    """Validate OpenAPI document structure and essential fields."""
    issues: List[ValidationIssue] = []

    # 1. Version check
    openapi_version = str(doc.get("openapi", "")).strip()
    if not openapi_version:
        # Check swagger 2.0
        if "swagger" in doc:
            issues.append(ValidationIssue(
                location="#/swagger",
                message="Swagger 2.0 is not supported. Please upgrade to OpenAPI 3.0 or 3.1.",
                severity=Severity.CRITICAL,
            ))
        else:
            issues.append(ValidationIssue(
                location="#/openapi",
                message="Missing required 'openapi' version field.",
                severity=Severity.CRITICAL,
            ))
    elif not (openapi_version.startswith("3.0") or openapi_version.startswith("3.1") or openapi_version.startswith("3.2")):
        issues.append(ValidationIssue(
            location="#/openapi",
            message=f"Unsupported OpenAPI version '{openapi_version}'. Supported versions: 3.0.x, 3.1.x.",
            severity=Severity.HIGH,
        ))

    # 2. Info object
    info = doc.get("info")
    title = None
    version = None
    if not isinstance(info, dict):
        issues.append(ValidationIssue(
            location="#/info",
            message="Missing or invalid required 'info' object.",
            severity=Severity.CRITICAL,
        ))
    else:
        title = info.get("title")
        version = info.get("version")
        if not title:
            issues.append(ValidationIssue(
                location="#/info/title",
                message="Info object is missing required 'title' string.",
                severity=Severity.HIGH,
            ))
        if not version:
            issues.append(ValidationIssue(
                location="#/info/version",
                message="Info object is missing required 'version' string.",
                severity=Severity.HIGH,
            ))

    # 3. Paths / components check
    paths = doc.get("paths")
    if paths is None and not (openapi_version.startswith("3.1") and ("webhooks" in doc or "components" in doc)):
        issues.append(ValidationIssue(
            location="#/paths",
            message="Document must contain a 'paths' object.",
            severity=Severity.CRITICAL,
        ))

    if isinstance(paths, dict):
        for path_key, path_item in paths.items():
            if not path_key.startswith("/"):
                issues.append(ValidationIssue(
                    location=f"#/paths/{path_key}",
                    message=f"Path '{path_key}' must begin with a forward slash '/'.",
                    severity=Severity.HIGH,
                ))

            if isinstance(path_item, dict):
                # Path level parameters
                path_params = path_item.get("parameters", [])
                if isinstance(path_params, list):
                    _validate_parameters(path_params, f"#/paths/{path_key}/parameters", doc, issues)

                for method, op in path_item.items():
                    method_lower = method.lower()
                    if method_lower in HTTP_METHODS and isinstance(op, dict):
                        op_loc = f"#/paths/{path_key}/{method}"
                        # Check operation responses
                        responses = op.get("responses")
                        if not isinstance(responses, dict) or not responses:
                            issues.append(ValidationIssue(
                                location=f"{op_loc}/responses",
                                message=f"Operation {method.upper()} {path_key} must contain a non-empty 'responses' object.",
                                severity=Severity.HIGH,
                            ))
                        else:
                            for status_code in responses.keys():
                                sc_str = str(status_code)
                                if sc_str != "default" and not (sc_str.isdigit() and len(sc_str) == 3):
                                    issues.append(ValidationIssue(
                                        location=f"{op_loc}/responses/{sc_str}",
                                        message=f"Response status code '{sc_str}' should be a 3-digit HTTP code or 'default'.",
                                        severity=Severity.MEDIUM,
                                    ))

                        # Operation parameters
                        op_params = op.get("parameters", [])
                        if isinstance(op_params, list):
                            _validate_parameters(op_params, f"{op_loc}/parameters", doc, issues)

    # 4. Reference checks
    _check_refs_in_doc(doc, doc, "#", issues)

    has_critical = any(i.severity in (Severity.CRITICAL, Severity.HIGH) for i in issues)
    return ValidationResult(
        is_valid=not has_critical,
        openapi_version=openapi_version,
        title=title,
        version=str(version) if version is not None else None,
        issues=issues,
    )


def _validate_parameters(params: List[Any], loc: str, doc: Dict[str, Any], issues: List[ValidationIssue]) -> None:
    for idx, param in enumerate(params):
        param_loc = f"{loc}/{idx}"
        resolved = param
        if isinstance(param, dict) and "$ref" in param:
            try:
                resolved = resolve_local_ref(param["$ref"], doc)
            except SpecRefError as err:
                issues.append(ValidationIssue(
                    location=f"{param_loc}/$ref",
                    message=f"Unresolved parameter reference: {err}",
                    severity=Severity.HIGH,
                ))
                continue

        if isinstance(resolved, dict):
            name = resolved.get("name")
            p_in = resolved.get("in")
            if not name:
                issues.append(ValidationIssue(
                    location=f"{param_loc}/name",
                    message="Parameter is missing required 'name' field.",
                    severity=Severity.HIGH,
                ))
            if not p_in or p_in not in VALID_PARAM_IN:
                issues.append(ValidationIssue(
                    location=f"{param_loc}/in",
                    message=f"Parameter 'in' field must be one of: {', '.join(sorted(VALID_PARAM_IN))}.",
                    severity=Severity.HIGH,
                ))


def _check_refs_in_doc(node: Any, root: Dict[str, Any], current_path: str, issues: List[ValidationIssue]) -> None:
    if isinstance(node, dict):
        if "$ref" in node and isinstance(node["$ref"], str):
            ref_str = node["$ref"]
            if ref_str.startswith("#/"):
                try:
                    resolve_local_ref(ref_str, root)
                except SpecRefError as err:
                    issues.append(ValidationIssue(
                        location=f"{current_path}/$ref",
                        message=f"Broken reference '{ref_str}': {err}",
                        severity=Severity.HIGH,
                    ))
            elif ref_str.startswith("http://") or ref_str.startswith("https://") or "/" in ref_str:
                issues.append(ValidationIssue(
                    location=f"{current_path}/$ref",
                    message=f"External reference '{ref_str}' is restricted.",
                    severity=Severity.MEDIUM,
                ))
        for k, v in node.items():
            _check_refs_in_doc(v, root, f"{current_path}/{k}", issues)
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            _check_refs_in_doc(item, root, f"{current_path}/{idx}", issues)
