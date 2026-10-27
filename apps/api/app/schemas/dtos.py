from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field
from api_contract_studio.models import DiffSummary, Finding, ValidationIssue


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    email: str
    full_name: Optional[str] = None
    created_at: datetime


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectOut(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    created_at: datetime
    contracts_count: int = 0


class ContractCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    initial_content: str
    version: str = "1.0.0"


class ContractUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class RevisionCreate(BaseModel):
    version: str = "1.0.0"
    content: str
    summary: Optional[str] = None


class RevisionOut(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    contract_id: str
    version: str
    content: str
    content_hash: str
    summary: Optional[str] = None
    created_at: datetime


class ContractOut(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    active_revision_id: Optional[str] = None
    active_version: Optional[str] = None
    revisions_count: int = 0
    created_at: datetime
    updated_at: datetime


class ValidateRequest(BaseModel):
    content: str


class ValidateResponse(BaseModel):
    is_valid: bool
    openapi_version: Optional[str] = None
    title: Optional[str] = None
    version: Optional[str] = None
    issues: List[ValidationIssue] = Field(default_factory=list)


class ComparisonRequest(BaseModel):
    baseline_content: str
    candidate_content: str
    policy: Optional[Dict[str, Any]] = None


class ComparisonOut(BaseModel):
    id: Optional[str] = None
    baseline_title: str
    baseline_version: str
    candidate_title: str
    candidate_version: str
    summary: DiffSummary
    findings: List[Finding]
    timestamp: str


class EnvironmentCreate(BaseModel):
    name: str
    base_url: str
    is_production: bool = False


class EnvironmentOut(BaseModel):
    model_config = {"from_attributes": True}
    id: str
    project_id: str
    name: str
    base_url: str
    is_production: bool
    created_at: datetime


class TestExecuteRequest(BaseModel):
    base_url: str
    allow_local: bool = True
    allow_non_idempotent: bool = False


class DashboardMetricsOut(BaseModel):
    total_projects: int
    total_contracts: int
    total_comparisons: int
    breaking_changes_detected: int
    validation_success_rate: float
    total_tests_run: int
    test_pass_rate: float
