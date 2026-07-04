from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.database import get_db
from app.models import Organization, OrganizationMember, User, OrgRole, new_uuid
from app.schemas import OrgCreate, OrgOut, MemberAdd
from app.auth import get_current_user

router = APIRouter(prefix="/api/orgs", tags=["organizations"])


@router.post("", response_model=OrgOut, status_code=201)
async def create_org(body: OrgCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    existing = await db.execute(select(Organization).where(Organization.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slug already taken")

    org = Organization(id=new_uuid(), name=body.name, slug=body.slug, created_by=user.id)
    db.add(org)
    await db.flush()

    # Add creator as owner
    member = OrganizationMember(org_id=org.id, user_id=user.id, role=OrgRole.owner)
    db.add(member)
    return org


@router.get("", response_model=List[OrgOut])
async def list_orgs(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Organization)
        .join(OrganizationMember, OrganizationMember.org_id == Organization.id)
        .where(OrganizationMember.user_id == user.id)
    )
    return result.scalars().all()


@router.get("/{org_id}", response_model=OrgOut)
async def get_org(org_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    org = await _get_org_or_404(org_id, db)
    await _require_membership(org_id, user.id, db)
    return org


@router.post("/{org_id}/members", status_code=201)
async def add_member(org_id: str, body: MemberAdd, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _require_role(org_id, user.id, [OrgRole.owner, OrgRole.admin], db)
    existing = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == body.user_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already a member")
    db.add(OrganizationMember(org_id=org_id, user_id=body.user_id, role=body.role))
    return {"message": "Member added"}


# ── Helpers ───────────────────────────────────────────────────────────────────
async def _get_org_or_404(org_id: str, db: AsyncSession) -> Organization:
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


async def _require_membership(org_id: str, user_id: str, db: AsyncSession):
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == user_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this organization")


async def _require_role(org_id: str, user_id: str, allowed_roles: list, db: AsyncSession):
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()
    if not member or member.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
