from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from ..core.db import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    owner = relationship("User", back_populates="projects")
    contracts = relationship("ApiContract", back_populates="project", cascade="all, delete-orphan")
    environments = relationship("Environment", back_populates="project", cascade="all, delete-orphan")


class ApiContract(Base):
    __tablename__ = "api_contracts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    active_revision_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    project = relationship("Project", back_populates="contracts")
    revisions = relationship("ContractRevision", back_populates="contract", cascade="all, delete-orphan")
    test_runs = relationship("TestRun", back_populates="contract", cascade="all, delete-orphan")


class ContractRevision(Base):
    __tablename__ = "contract_revisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    contract_id = Column(String(36), ForeignKey("api_contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(50), nullable=False, default="1.0.0")
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    author_id = Column(String(36), nullable=True)
    summary = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    contract = relationship("ApiContract", back_populates="revisions")


class ContractComparison(Base):
    __tablename__ = "contract_comparisons"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    baseline_revision_id = Column(String(36), nullable=True)
    candidate_revision_id = Column(String(36), nullable=True)
    summary_json = Column(Text, nullable=False)  # JSON serialized DiffSummary
    passed_policy = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    findings = relationship("ComparisonFinding", back_populates="comparison", cascade="all, delete-orphan")


class ComparisonFinding(Base):
    __tablename__ = "comparison_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    comparison_id = Column(String(36), ForeignKey("contract_comparisons.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    compatibility = Column(String(30), nullable=False)
    location = Column(String(255), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    message = Column(Text, nullable=False)
    remediation = Column(Text, nullable=False)
    fails_ci = Column(Boolean, default=False)

    comparison = relationship("ContractComparison", back_populates="findings")


class Environment(Base):
    __tablename__ = "environments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    base_url = Column(String(255), nullable=False)
    is_production = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    project = relationship("Project", back_populates="environments")


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    contract_id = Column(String(36), ForeignKey("api_contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    environment_id = Column(String(36), nullable=True)
    base_url = Column(String(255), nullable=False)
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    report_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    contract = relationship("ApiContract", back_populates="test_runs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(36), nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
