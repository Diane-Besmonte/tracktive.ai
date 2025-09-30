from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# ===== Schemas =====
class UserCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=2, max_length=120)
    username: constr(strip_whitespace=True, min_length=3, max_length=60)
    email: EmailStr
    password: constr(min_length=8, max_length=128)

class UserPublic(BaseModel):
    id: int
    name: str
    username: str
    email: EmailStr

class LoginRequest(BaseModel):
    username_or_email: constr(strip_whitespace=True, min_length=3, max_length=255)
    password: constr(min_length=8, max_length=128)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic

def _to_public(u: User) -> UserPublic:
    return UserPublic(id=u.id, name=u.name, username=u.username, email=u.email)

# ===== Endpoints =====
@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == body.username.lower()) | (User.email == body.email.lower())).first():
        raise HTTPException(status_code=400, detail="Username or email already taken")
    u = User(
        name=body.name,
        username=body.username.lower(),
        email=body.email.lower(),
        password_hash=hash_password(body.password),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    token = create_access_token(sub=str(u.id))
    return TokenResponse(access_token=token, user=_to_public(u))

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    u = db.query(User).filter(
        (User.username == body.username_or_email.lower()) | (User.email == body.username_or_email.lower())
    ).first()
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(sub=str(u.id))
    return TokenResponse(access_token=token, user=_to_public(u))

@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)):
    return _to_public(current_user)

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    # JWT is stateless; client deletes the token. This just verifies auth.
    return {"ok": True}
