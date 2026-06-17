import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models import User, UserProfile
from app.schemas import LoginRequest, ProfileUpdate, RegisterRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.flush()

    profile = UserProfile(
        user_id=user.id,
        role_targets_json=json.dumps(["Data Engineer", "AI Engineer"]),
        skills_json=json.dumps([]),
        projects_json=json.dumps([]),
        languages_json=json.dumps({"English": "fluent"}),
    )
    db.add(profile)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        plan=user.plan.value,
        email=user.email,
        full_name=user.full_name,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        plan=user.plan.value,
        email=user.email,
        full_name=user.full_name,
    )


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "plan": user.plan.value,
        "profile_complete": bool(profile and profile.skills_json and profile.skills_json != "[]"),
    }


@router.get("/profile")
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _profile_dict(profile)


@router.put("/profile")
def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile.headline = payload.headline
    profile.location = payload.location
    profile.visa_status = payload.visa_status
    profile.linkedin = payload.linkedin
    profile.github = payload.github
    profile.phone = payload.phone
    profile.certification = payload.certification
    profile.summary = payload.summary
    profile.stack_highlight = payload.stack_highlight
    profile.skills_json = json.dumps(payload.skills)
    profile.projects_json = json.dumps(payload.projects)
    profile.languages_json = json.dumps(payload.languages)
    profile.role_targets_json = json.dumps(payload.role_targets)
    profile.relocation_targets_json = json.dumps(payload.relocation_targets)
    db.commit()
    return _profile_dict(profile)


def _profile_dict(profile: UserProfile) -> dict:
    return {
        "headline": profile.headline,
        "location": profile.location,
        "visa_status": profile.visa_status,
        "linkedin": profile.linkedin,
        "github": profile.github,
        "phone": profile.phone,
        "certification": profile.certification,
        "summary": profile.summary,
        "stack_highlight": profile.stack_highlight,
        "skills": json.loads(profile.skills_json or "[]"),
        "projects": json.loads(profile.projects_json or "[]"),
        "languages": json.loads(profile.languages_json or "{}"),
        "role_targets": json.loads(profile.role_targets_json or "[]"),
        "relocation_targets": json.loads(profile.relocation_targets_json or "[]"),
    }