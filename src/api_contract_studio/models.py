from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Compatibility(str, Enum):
    BREAKING = "BREAKING"
    POTENTIALLY_BREAKING = "POTENTIALLY_BREAKING"
    NON_BREAKING = "NON_BREAKING"
    INFORMATIONAL = "INFORMATIONAL"


class ChangeCategory(str, Enum):
    ENDPOINT = "endpoint"
    REQUEST = "request"
    RESPONSE = "response"
    SCHEMA = "schema"
    SECURITY = "security"
    METADATA = "metadata"


class Finding(BaseModel):
    rule_id: str
    category: ChangeCategory
    severity: Severity
    compatibility: Compatibility
    location: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    message: str
    remediation: str
    fails_ci: bool = False


class PolicyConfig(BaseModel):
    fail_on: List[Compatibility] = Field(default_factory=lambda: [Compatibility.BREAKING])
    potentially_breaking: str = "warn"  # "fail", "warn", "ignore"
    severity_threshold: Severity = Severity.HIGH
    allowed_rules: List[str] = Field(default_factory=list)
    ignored_rules: List[str] = Field(default_factory=list)


class DiffSummary(BaseModel):
    total_changes: int = 0
    breaking_count: int = 0
    potentially_breaking_count: int = 0
    non_breaking_count: int = 0
    informational_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    passed_policy: bool = True


class DiffReport(BaseModel):
    baseline_title: str = "Baseline"
    baseline_version: str = "1.0.0"
    candidate_title: str = "Candidate"
    candidate_version: str = "1.0.0"
    summary: DiffSummary = Field(default_factory=DiffSummary)
    findings: List[Finding] = Field(default_factory=list)
    timestamp: Optional[str] = None


class ValidationIssue(BaseModel):
    location: str
    message: str
    severity: Severity = Severity.HIGH


class ValidationResult(BaseModel):
    is_valid: bool
    openapi_version: Optional[str] = None
    title: Optional[str] = None
    version: Optional[str] = None
    issues: List[ValidationIssue] = Field(default_factory=list)


class TestResultItem(BaseModel):
    endpoint: str
    method: str
    expected_status: int
    observed_status: int
    passed: bool
    duration_ms: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class TestSuiteReport(BaseModel):
    base_url: str
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    duration_seconds: float = 0.0
    results: List[TestResultItem] = Field(default_factory=list)
    timestamp: str = ""
