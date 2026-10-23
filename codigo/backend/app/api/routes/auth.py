from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import login_user, register_user
from app.core.deployment import auth_attempt, production

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/configuration")
def configuration():
    # Public UI policy only: never expose member emails or private settings.
    return {"public_registration_enabled": not production()}


@router.post("/register", response_model=UserResponse)
def register(data: UserCreate, request: Request, db: Session = Depends(get_db)):
    auth_attempt(request.client.host if request.client else "unknown", str(data.email))
    return register_user(db, data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    auth_attempt(request.client.host if request.client else "unknown", data.username_or_email)
    return login_user(db, data)
