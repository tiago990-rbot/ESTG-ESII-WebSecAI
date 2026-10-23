"""Run ONLY in a person's private console: the generated link is a credential."""
from getpass import getpass, GetPassWarning
from pathlib import Path
import os
import sys
import warnings

FRONTEND = "https://websecai-frontend.websecai-estg.workers.dev"
ACCOUNTS = {"1": ("goncalofazendeirocordeiro@gmail.com", "invite"),
            "2": ("tmelo1715@gmail.com", "reset"),
            "3": ("goncalofazendeirocordeiro@gmail.com", "reset")}


def main():
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Executa pessoalmente numa consola privada. Nao enviar a saida ao assistente.")
        return 1
    warnings.simplefilter("error", GetPassWarning)
    print("1 - Convite para o Goncalo (conta nova ou convite pendente)")
    print("2 - Repor a minha password WebSecAI (Tiago)")
    print("3 - Repor a password do Goncalo (conta ja ativa)")
    choice = input("Escolhe 1, 2 ou 3; outra tecla cancela: ").strip()
    if choice not in ACCOUNTS:
        print("Cancelado. Nada foi alterado.")
        return 1
    email, purpose = ACCOUNTS[choice]
    print("Destinatario: " + email)
    print("Confirma a identidade da pessoa antes de lhe enviares um link.")
    print("No Neon: WebSecCheckAI / websecai-validacao / Connect / pooling DESLIGADO.")
    direct = getpass("Ligacao direta Neon (oculta): ").strip()
    if not direct:
        return 1
    # Do not read any .env files; the human supplies the only connection used.
    import dotenv
    dotenv.load_dotenv = lambda *args, **kwargs: False
    os.environ.update(DATABASE_URL=direct, DATABASE_MIGRATION_URL=direct,
                      APP_ENV="production", APP_ALLOWED_EMAILS=",".join(sorted({x[0] for x in ACCOUNTS.values()})))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from sqlalchemy.orm import Session
    from app.db.configuration import database_url, build_engine
    from app.services.account_access import issue_account_link
    from app.models import scan, finding, investigation
    url = database_url(direct)
    if (url.get_backend_name() != "postgresql" or not url.username or not url.password
            or not url.database or not (url.host or "").endswith(".neon.tech") or "-pooler" in (url.host or "")):
        print("Usa apenas a ligacao direta oficial Neon indicada. Nada foi alterado.")
        return 1
    username = input("Nome de utilizador para a conta nova: ").strip() if purpose == "invite" else ""
    if input("Escreve EMITIR para criar o link privado: ").strip() != "EMITIR":
        print("Cancelado. Nada foi alterado.")
        return 1
    engine = build_engine(url, migration=True)
    try:
        with Session(engine) as db:
            token = issue_account_link(db, email, purpose, username)
    finally:
        engine.dispose()
    print("Link de uso unico. Expira em " + ("24 horas." if purpose == "invite" else "30 minutos."))
    print("O link anterior desta conta foi invalidado. A password atual ainda nao mudou.")
    print("Copia e envia TU o link completo apenas ao destinatario. Nao o envies ao modelo.")
    print(FRONTEND + "/reset-password#token=" + token)
    print("A pessoa abre o link no site e escolhe a password em privado. Nunca enviar uma password padrao.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, EOFError):
        print("Operacao interrompida. Nenhuma credencial foi apresentada.")
        raise SystemExit(1)
    except Exception:
        print("Nao foi possivel emitir o link. Confirma que o deploy novo esta Live, a branch e o tipo de conta estao corretos.")
        print("Nao envies a ligacao ou capturas. Uma conta ativa usa reposicao, nao convite.")
        raise SystemExit(1)
