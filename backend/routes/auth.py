from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from backend.database import get_db
from backend.models import User, Organization, Project, RetryPolicy, OrganizationUser
from backend.schemas import (
    UserCreate, UserResponse, Token, OrganizationCreate, OrganizationResponse,
    ProjectCreate, ProjectResponse, RetryPolicyCreate, RetryPolicyResponse
)
from backend.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.username == user_in.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed = hash_password(user_in.password)
    user = User(username=user_in.username, password_hash=hashed, role=user_in.role or "user")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post("/login", response_model=Token)
async def login(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.username == user_in.username))
    user = result.scalars().first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    token = create_access_token({"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user

# Organizations API
@router.post("/organizations", response_model=OrganizationResponse)
async def create_organization(
    org_in: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    org = Organization(name=org_in.name)
    db.add(org)
    await db.commit()
    await db.refresh(org)
    
    # Associate user
    org_user = OrganizationUser(organization_id=org.id, user_id=current_user.id, role="admin")
    db.add(org_user)
    await db.commit()
    
    return org

@router.get("/organizations", response_model=List[OrganizationResponse])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # If admin, return all. Otherwise return only user's orgs.
    if current_user.role == "admin":
        result = await db.execute(select(Organization))
        return result.scalars().all()
    
    result = await db.execute(
        select(Organization)
        .join(OrganizationUser)
        .filter(OrganizationUser.user_id == current_user.id)
    )
    return result.scalars().all()

# Projects API
@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify user belongs to organization
    if current_user.role != "admin":
        assoc = await db.execute(
            select(OrganizationUser)
            .filter(
                OrganizationUser.organization_id == project_in.organization_id,
                OrganizationUser.user_id == current_user.id
            )
        )
        if not assoc.scalars().first():
            raise HTTPException(status_code=403, detail="Not authorized for this organization")

    project = Project(organization_id=project_in.organization_id, name=project_in.name)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        result = await db.execute(select(Project))
        return result.scalars().all()

    result = await db.execute(
        select(Project)
        .join(Organization)
        .join(OrganizationUser)
        .filter(OrganizationUser.user_id == current_user.id)
    )
    return result.scalars().all()

# Retry Policies API
@router.post("/retry-policies", response_model=RetryPolicyResponse)
async def create_retry_policy(
    policy_in: RetryPolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    policy = RetryPolicy(
        name=policy_in.name,
        strategy=policy_in.strategy,
        base_delay=policy_in.base_delay,
        max_retries=policy_in.max_retries,
        backoff_factor=policy_in.backoff_factor
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy

@router.get("/retry-policies", response_model=List[RetryPolicyResponse])
async def list_retry_policies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RetryPolicy))
    return result.scalars().all()
