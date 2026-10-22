from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate
from app.core.deployment import check_member, production


def register_user(db: Session, data: UserCreate) -> User:
    if production():
        raise HTTPException(403, "Registo público fechado. As contas do grupo são criadas privadamente pelo responsável.")
    username, email = data.username.strip(), str(data.email).strip().lower()
    check_member(email)
    existing = db.query(User).filter(or_(User.username == username, User.email == email)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username ou email já existe")
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, data: LoginRequest) -> TokenResponse:
    identifier = data.username_or_email.strip().lower()
    user = db.query(User).filter(or_(User.username == data.username_or_email.strip(), User.email == identifier)).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    check_member(user.email)
    if user.password_hash.startswith("pbkdf2_sha256$"):
        user.password_hash = hash_password(data.password)
        db.commit()
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)
