from __future__ import annotations

import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api_contract_studio.models import TestSuiteReport
from api_contract_studio.parser import parse_spec_content
from api_contract_studio.tester import SSRFValidationError, run_contract_test
from ...core.db import get_db
from ...models.entities import ApiContract, ContractRevision, Project, TestRun, User
from ...schemas.dtos import TestExecuteRequest
from ..deps import get_current_user

router = APIRouter(tags=["tests"])


@router.post("/contracts/{contract_id}/test", response_model=TestSuiteReport)
def execute_contract_test(
    contract_id: str,
    req: TestExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(ApiContract).join(Project).filter(
        ApiContract.id == contract_id,
        Project.owner_id == current_user.id,
    ).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")

    if not contract.active_revision_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contract has no active revisions.")

    active_rev = db.query(ContractRevision).filter(ContractRevision.id == contract.active_revision_id).first()
    if not active_rev:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active revision not found.")

    try:
        spec_doc = parse_spec_content(active_rev.content, source_name="active_spec")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to parse active contract specification: {e}")

    try:
        report = run_contract_test(
            spec_doc,
            base_url=req.base_url,
            allow_local=req.allow_local,
            allow_non_idempotent=req.allow_non_idempotent,
        )
    except SSRFValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"SSRF security violation: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Contract test execution error: {e}")

    # Persist TestRun
    test_run = TestRun(
        contract_id=contract.id,
        base_url=report.base_url,
        total_tests=report.total_tests,
        passed_tests=report.passed_tests,
        failed_tests=report.failed_tests,
        duration_seconds=report.duration_seconds,
        report_json=json.dumps(report.model_dump()),
    )
    db.add(test_run)
    db.commit()

    return report


@router.get("/test-runs/{test_run_id}", response_model=TestSuiteReport)
def get_test_run(
    test_run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = db.query(TestRun).join(ApiContract).join(Project).filter(
        TestRun.id == test_run_id,
        Project.owner_id == current_user.id,
    ).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test run not found.")

    return TestSuiteReport(**json.loads(run.report_json))
