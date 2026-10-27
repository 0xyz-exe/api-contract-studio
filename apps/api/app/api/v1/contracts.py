from __future__ import annotations

import hashlib
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.db import get_db
from ...models.entities import ApiContract, ContractRevision, Project, User
from ...schemas.dtos import ContractCreate, ContractOut, ContractUpdate, RevisionCreate, RevisionOut
from ..deps import get_current_user

router = APIRouter(tags=["contracts"])


def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()


@router.get("/projects/{project_id}/contracts", response_model=List[ContractOut])
def list_contracts(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    results = []
    for c in project.contracts:
        active_rev = None
        if c.active_revision_id:
            active_rev = db.query(ContractRevision).filter(ContractRevision.id == c.active_revision_id).first()
        results.append(
            ContractOut(
                id=c.id,
                project_id=c.project_id,
                name=c.name,
                description=c.description,
                active_revision_id=c.active_revision_id,
                active_version=active_rev.version if active_rev else "1.0.0",
                revisions_count=len(c.revisions),
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
        )
    return results


@router.post("/projects/{project_id}/contracts", response_model=ContractOut, status_code=status.HTTP_201_CREATED)
def create_contract(
    project_id: str,
    contract_in: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    contract = ApiContract(
        project_id=project.id,
        name=contract_in.name,
        description=contract_in.description,
    )
    db.add(contract)
    db.flush()

    # Create initial immutable revision
    rev_hash = compute_sha256(contract_in.initial_content)
    initial_rev = ContractRevision(
        contract_id=contract.id,
        version=contract_in.version,
        content=contract_in.initial_content,
        content_hash=rev_hash,
        author_id=current_user.id,
        summary="Initial contract import",
    )
    db.add(initial_rev)
    db.flush()

    contract.active_revision_id = initial_rev.id
    db.commit()
    db.refresh(contract)

    return ContractOut(
        id=contract.id,
        project_id=contract.project_id,
        name=contract.name,
        description=contract.description,
        active_revision_id=contract.active_revision_id,
        active_version=initial_rev.version,
        revisions_count=1,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
    )


@router.get("/contracts/{contract_id}", response_model=ContractOut)
def get_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(ApiContract).join(Project).filter(
        ApiContract.id == contract_id,
        Project.owner_id == current_user.id,
    ).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")

    active_rev = None
    if contract.active_revision_id:
        active_rev = db.query(ContractRevision).filter(ContractRevision.id == contract.active_revision_id).first()

    return ContractOut(
        id=contract.id,
        project_id=contract.project_id,
        name=contract.name,
        description=contract.description,
        active_revision_id=contract.active_revision_id,
        active_version=active_rev.version if active_rev else "1.0.0",
        revisions_count=len(contract.revisions),
        created_at=contract.created_at,
        updated_at=contract.updated_at,
    )


@router.delete("/contracts/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(ApiContract).join(Project).filter(
        ApiContract.id == contract_id,
        Project.owner_id == current_user.id,
    ).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")
    db.delete(contract)
    db.commit()
    return None


@router.get("/contracts/{contract_id}/revisions", response_model=List[RevisionOut])
def list_contract_revisions(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(ApiContract).join(Project).filter(
        ApiContract.id == contract_id,
        Project.owner_id == current_user.id,
    ).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")

    revisions = (
        db.query(ContractRevision)
        .filter(ContractRevision.contract_id == contract.id)
        .order_by(ContractRevision.created_at.desc())
        .all()
    )
    return revisions


@router.post("/contracts/{contract_id}/revisions", response_model=RevisionOut, status_code=status.HTTP_201_CREATED)
def create_contract_revision(
    contract_id: str,
    rev_in: RevisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(ApiContract).join(Project).filter(
        ApiContract.id == contract_id,
        Project.owner_id == current_user.id,
    ).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")

    content_hash = compute_sha256(rev_in.content)
    # Check if duplicate of latest revision
    latest_rev = (
        db.query(ContractRevision)
        .filter(ContractRevision.contract_id == contract.id)
        .order_by(ContractRevision.created_at.desc())
        .first()
    )
    if latest_rev and latest_rev.content_hash == content_hash:
        return latest_rev

    new_rev = ContractRevision(
        contract_id=contract.id,
        version=rev_in.version,
        content=rev_in.content,
        content_hash=content_hash,
        author_id=current_user.id,
        summary=rev_in.summary or f"Updated to version {rev_in.version}",
    )
    db.add(new_rev)
    db.flush()

    contract.active_revision_id = new_rev.id
    db.commit()
    db.refresh(new_rev)
    return new_rev


@router.post("/contracts/{contract_id}/revisions/{revision_id}/restore", response_model=RevisionOut)
def restore_contract_revision(
    contract_id: str,
    revision_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(ApiContract).join(Project).filter(
        ApiContract.id == contract_id,
        Project.owner_id == current_user.id,
    ).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")

    target_rev = db.query(ContractRevision).filter(
        ContractRevision.id == revision_id,
        ContractRevision.contract_id == contract.id,
    ).first()
    if not target_rev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target revision not found.")

    # Rule: Restore operations must create a new revision rather than rewriting history.
    new_rev = ContractRevision(
        contract_id=contract.id,
        version=f"{target_rev.version}-restored",
        content=target_rev.content,
        content_hash=target_rev.content_hash,
        author_id=current_user.id,
        summary=f"Restored from revision {target_rev.id[:8]} (v{target_rev.version})",
    )
    db.add(new_rev)
    db.flush()

    contract.active_revision_id = new_rev.id
    db.commit()
    db.refresh(new_rev)
    return new_rev
