from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, ChangePasswordRequest, ResetPasswordRequest
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import login_user, register_user
from app.core.deployment import auth_attempt, production
from app.core.security import get_current_user
from app.models.user import User
from app.services.account_access import change_password, redeem_account_link

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


@router.post("/password/change", status_code=204)
def password_change(data: ChangePasswordRequest, request: Request,
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    auth_attempt(request.client.host if request.client else "unknown", "password:" + user.email)
    change_password(db, user, data.current_password, data.new_password, data.confirmation)
    return Response(status_code=204, headers={"Cache-Control": "no-store"})


@router.post("/password/reset", status_code=204)
def password_reset(data: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    auth_attempt(request.client.host if request.client else "unknown", "reset:" + data.token)
    redeem_account_link(db, data.token, data.new_password, data.confirmation)
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
