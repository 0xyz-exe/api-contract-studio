from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api_contract_studio.comparator import compare_specs
from api_contract_studio.models import PolicyConfig, Severity, ValidationIssue
from api_contract_studio.parser import SpecParseError, parse_spec_content
from api_contract_studio.validator import validate_openapi_spec
from ...core.db import get_db
from ...models.entities import ComparisonFinding, ContractComparison, User
from ...schemas.dtos import ComparisonOut, ComparisonRequest, ValidateRequest, ValidateResponse
from ..deps import get_optional_user

router = APIRouter(tags=["comparisons"])


@router.post("/contracts/validate", response_model=ValidateResponse)
def validate_contract_spec(req: ValidateRequest):
    try:
        doc = parse_spec_content(req.content, source_name="uploaded_spec")
    except SpecParseError as err:
        return ValidateResponse(
            is_valid=False,
            openapi_version=None,
            title=None,
            version=None,
            issues=[ValidationIssue(location="#/root", message=str(err), severity=Severity.CRITICAL)],
        )

    res = validate_openapi_spec(doc)
    return ValidateResponse(
        is_valid=res.is_valid,
        openapi_version=res.openapi_version,
        title=res.title,
        version=res.version,
        issues=res.issues,
    )


@router.post("/contracts/compare", response_model=ComparisonOut)
def compare_contract_specs(
    req: ComparisonRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    try:
        base_doc = parse_spec_content(req.baseline_content, source_name="baseline")
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse baseline specification: {err}",
        )

    try:
        cand_doc = parse_spec_content(req.candidate_content, source_name="candidate")
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse candidate specification: {err}",
        )

    policy_cfg = PolicyConfig(**(req.policy or {})) if req.policy else PolicyConfig()
    diff_report = compare_specs(base_doc, cand_doc, policy=policy_cfg)

    # Persist comparison in database
    comparison_rec = ContractComparison(
        summary_json=json.dumps(diff_report.summary.model_dump()),
        passed_policy=diff_report.summary.passed_policy,
    )
    db.add(comparison_rec)
    db.flush()

    for f in diff_report.findings:
        finding_rec = ComparisonFinding(
            comparison_id=comparison_rec.id,
            rule_id=f.rule_id,
            category=f.category.value,
            severity=f.severity.value,
            compatibility=f.compatibility.value,
            location=f.location,
            old_value=f.old_value,
            new_value=f.new_value,
            message=f.message,
            remediation=f.remediation,
            fails_ci=f.fails_ci,
        )
        db.add(finding_rec)

    db.commit()

    return ComparisonOut(
        id=comparison_rec.id,
        baseline_title=diff_report.baseline_title,
        baseline_version=diff_report.baseline_version,
        candidate_title=diff_report.candidate_title,
        candidate_version=diff_report.candidate_version,
        summary=diff_report.summary,
        findings=diff_report.findings,
        timestamp=diff_report.timestamp or datetime.now(timezone.utc).isoformat(),
    )


@router.get("/comparisons/{comparison_id}", response_model=ComparisonOut)
def get_comparison(
    comparison_id: str,
    db: Session = Depends(get_db),
):
    comparison = db.query(ContractComparison).filter(ContractComparison.id == comparison_id).first()
    if not comparison:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comparison report not found.")

    summary_dict = json.loads(comparison.summary_json)
    findings_list = []
    for f in comparison.findings:
        findings_list.append({
            "rule_id": f.rule_id,
            "category": f.category,
            "severity": f.severity,
            "compatibility": f.compatibility,
            "location": f.location,
            "old_value": f.old_value,
            "new_value": f.new_value,
            "message": f.message,
            "remediation": f.remediation,
            "fails_ci": f.fails_ci,
        })

    return ComparisonOut(
        id=comparison.id,
        baseline_title="Baseline Spec",
        baseline_version="1.0.0",
        candidate_title="Candidate Spec",
        candidate_version="1.0.0",
        summary=summary_dict,
        findings=findings_list,
        timestamp=comparison.created_at.isoformat(),
    )
