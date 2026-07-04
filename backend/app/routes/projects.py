from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import Project, Organization, OrganizationMember, RetryPolicy, new_uuid
from app.schemas import ProjectCreate, ProjectOut, RetryPolicyCreate, RetryPolicyOut
from app.auth import get_current_user
from app.models import User

router = APIRouter(tags=["projects"])


@router.post("/api/orgs/{org_id}/projects", response_model=ProjectOut, status_code=201)
async def create_project(
    org_id: str, body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    await _require_membership(org_id, user.id, db)
    existing = await db.execute(
        select(Project).where(Project.org_id == org_id, Project.slug == body.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slug already exists in this org")

    project = Project(
        id=new_uuid(), org_id=org_id, name=body.name,
        slug=body.slug, description=body.description, created_by=user.id
    )
    db.add(project)
    return project


@router.get("/api/orgs/{org_id}/projects", response_model=List[ProjectOut])
async def list_projects(
    org_id: str, db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    await _require_membership(org_id, user.id, db)
    result = await db.execute(select(Project).where(Project.org_id == org_id))
    return result.scalars().all()


@router.get("/api/projects/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str, db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    project = await _get_project_or_404(project_id, db)
    await _require_membership(project.org_id, user.id, db)
    return project


# ── Retry Policies ────────────────────────────────────────────────────────────
@router.post("/api/retry-policies", response_model=RetryPolicyOut, status_code=201)
async def create_retry_policy(
    body: RetryPolicyCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    policy = RetryPolicy(id=new_uuid(), **body.model_dump())
    db.add(policy)
    return policy


@router.get("/api/retry-policies", response_model=List[RetryPolicyOut])
async def list_retry_policies(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(RetryPolicy))
    return result.scalars().all()


# ── Helpers ───────────────────────────────────────────────────────────────────
async def _get_project_or_404(project_id: str, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def _require_membership(org_id: str, user_id: str, db: AsyncSession):
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == user_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this organization")
