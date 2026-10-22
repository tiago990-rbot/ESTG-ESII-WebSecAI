"""Human-only terminal: credentials go to getpass, never to the assistant."""
from getpass import getpass
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    # A person prepares this private file; do not print it or pass URLs on the CLI.
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env.production", override=True)
    from app.core.deployment import production, allowed_emails, validate_deployment
    from app.core.security import hash_password
    from app.db.configuration import migration_url, build_engine
    from app.db.migrate import upgrade_schema
    from app.models.user import User
    from app.schemas.user import UserCreate
    from sqlalchemy.orm import Session
    if not production():
        raise RuntimeError("Configure APP_ENV=production no ficheiro privado .env.production.")
    validate_deployment()
    upgrade_schema()
    engine = build_engine(migration_url(), migration=True)
    for email in sorted(allowed_emails()):
        with Session(engine) as db:
            if db.query(User).filter(User.email == email).first():
                print("Conta existente preservada.")
                continue
            username = input(f"Nome de utilizador para {email}: ").strip()
            password = getpass("Palavra-passe inicial (oculta): ")
            if password != getpass("Repetir palavra-passe (oculta): "):
                raise ValueError("Palavras-passe diferentes.")
            data = UserCreate(username=username, email=email, password=password)
            db.add(User(username=data.username, email=email, password_hash=hash_password(data.password)))
            db.commit()
            print("Conta criada. Nenhuma credencial foi apresentada.")
    engine.dispose()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("Provisionamento interrompido. Reveja os dados/configuração privadamente; contas existentes foram preservadas.")
        sys.exit(1)
