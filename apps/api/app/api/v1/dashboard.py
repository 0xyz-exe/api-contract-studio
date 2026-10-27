from __future__ import annotations

import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.db import get_db
from ...models.entities import ApiContract, ContractComparison, Project, TestRun, User
from ...schemas.dtos import DashboardMetricsOut
from ..deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardMetricsOut)
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_projects = db.query(Project).filter(Project.owner_id == current_user.id).count()
    total_contracts = (
        db.query(ApiContract)
        .join(Project)
        .filter(Project.owner_id == current_user.id)
        .count()
    )
    comparisons = db.query(ContractComparison).all()
    total_comparisons = len(comparisons)

    breaking_changes_count = 0
    valid_comparisons = 0
    for comp in comparisons:
        try:
            summary = json.loads(comp.summary_json)
            breaking_changes_count += summary.get("breaking_count", 0)
            if summary.get("passed_policy", True):
                valid_comparisons += 1
        except Exception:
            pass

    validation_success_rate = (
        round((valid_comparisons / total_comparisons) * 100, 1) if total_comparisons > 0 else 100.0
    )

    test_runs = (
        db.query(TestRun)
        .join(ApiContract)
        .join(Project)
        .filter(Project.owner_id == current_user.id)
        .all()
    )
    total_tests_run = sum(r.total_tests for r in test_runs)
    total_passed_tests = sum(r.passed_tests for r in test_runs)
    test_pass_rate = (
        round((total_passed_tests / total_tests_run) * 100, 1) if total_tests_run > 0 else 100.0
    )

    return DashboardMetricsOut(
        total_projects=total_projects,
        total_contracts=total_contracts,
        total_comparisons=total_comparisons,
        breaking_changes_detected=breaking_changes_count,
        validation_success_rate=validation_success_rate,
        total_tests_run=total_tests_run,
        test_pass_rate=test_pass_rate,
    )
