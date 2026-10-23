"""Single-use links are issued only in a human administrator's private console."""
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session
from app.core.deployment import check_member
from app.core.security import hash_password, verify_password
from app.models.account_action import AccountAction
from app.models.user import User

INVALID_LINK = "Link inválido, expirado ou já utilizado. Pede um novo ao responsável."


def digest_token(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def issue_account_link(db: Session, email: str, purpose: str, username: str = "") -> str:
    """Administrative function, deliberately not exposed through a public API."""
    email = email.strip().lower()
    check_member(email)
    if purpose not in {"invite", "reset"}:
        raise ValueError("Tipo de link inválido.")
    user = db.scalar(select(User).where(User.email == email).with_for_update())
    if purpose == "invite":
        if user and user.password_ready:
            raise ValueError("Conta já ativa. Usa a opção de reposição, depois de confirmar a identidade.")
        if not user:
            if not 3 <= len(username.strip()) <= 80:
                raise ValueError("Nome de utilizador inválido.")
            user = User(username=username.strip(), email=email,
                        password_hash=hash_password(secrets.token_urlsafe(48)), password_ready=False)
            db.add(user)
            db.flush()
    elif not user or not user.password_ready:
        raise ValueError("Conta sem acesso ativo. Usa um convite para uma conta nova.")
    db.execute(delete(AccountAction).where(AccountAction.user_id == user.id))
    # Keep the current password/session valid until the new link is redeemed.
    token = secrets.token_urlsafe(32)
    lifetime = timedelta(hours=24) if purpose == "invite" else timedelta(minutes=30)
    db.add(AccountAction(token_hash=digest_token(token), user_id=user.id, purpose=purpose,
                         auth_version=user.auth_version, expires_at=datetime.now(timezone.utc) + lifetime))
    db.commit()
    return token


def replace_password(db: Session, user: User, new_password: str):
    previous_version = user.auth_version
    result = db.execute(update(User).where(User.id == user.id, User.auth_version == previous_version,
                                          User.password_hash == user.password_hash).values(
        password_hash=hash_password(new_password), auth_version=previous_version + 1,
        password_ready=True), execution_options={"synchronize_session": False})
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(400, "A conta mudou entretanto. Inicia novamente o processo.")
    db.execute(delete(AccountAction).where(AccountAction.user_id == user.id))
    db.commit()


def check_confirmation(new_password: str, confirmation: str):
    if new_password != confirmation:
        raise HTTPException(400, "As novas palavras-passe não coincidem.")


def change_password(db: Session, user: User, current_password: str, new_password: str, confirmation: str):
    check_confirmation(new_password, confirmation)
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(400, "Palavra-passe atual incorreta.")
    if verify_password(new_password, user.password_hash):
        raise HTTPException(400, "Escolhe uma palavra-passe diferente da atual.")
    replace_password(db, user, new_password)


def redeem_account_link(db: Session, token: str, new_password: str, confirmation: str):
    check_confirmation(new_password, confirmation)
    action = db.get(AccountAction, digest_token(token))
    if action is None or action.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(400, INVALID_LINK)
    user = db.get(User, action.user_id)
    if (user is None or action.purpose not in {"invite", "reset"}
            or user.auth_version != action.auth_version
            or (action.purpose == "invite" and user.password_ready)
            or (action.purpose == "reset" and not user.password_ready)):
        raise HTTPException(400, INVALID_LINK)
    check_member(user.email)
    if verify_password(new_password, user.password_hash):
        raise HTTPException(400, "Escolhe uma palavra-passe diferente da atual.")
    consumed = db.execute(delete(AccountAction).where(
        AccountAction.token_hash == action.token_hash,
        AccountAction.expires_at > datetime.now(timezone.utc)),
        execution_options={"synchronize_session": False})
    if consumed.rowcount != 1:
        db.rollback()
        raise HTTPException(400, INVALID_LINK)
    replace_password(db, user, new_password)
