"""Connection policy shared by the application and Alembic; never log URLs."""
import certifi
import shlex
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool
from app.core.config import ROOT, value


def database_url(raw=None):
    raw = raw if raw is not None else value("DATABASE_URL", "sqlite:///" + (ROOT / "websec_check.db").as_posix())
    try:
        # Neon offers both a URL and a quoted psql snippet. Parse text only;
        # never execute commands or include connection data in an exception.
        if isinstance(raw, str):
            raw = raw.strip()
            if raw.startswith(("psql ", "psql\t", "'", '"')):
                parts = shlex.split(raw)
                if len(parts) == 2 and parts[0] == "psql":
                    raw = parts[1]
                elif len(parts) == 1 and not raw.startswith("psql"):
                    raw = parts[0]
                else:
                    raise ValueError("Expected one connection URL")
        url = make_url(raw)
    except Exception:
        raise RuntimeError("URL da base inválida; reveja a configuração privada.") from None
    if url.drivername in {"postgres", "postgresql", "postgresql+psycopg"}:
        url = url.set(drivername="postgresql+psycopg")
        # Certificate and hostname verification is mandatory outside local tests.
        if url.host not in {"127.0.0.1", "localhost", "::1"}:
            mode = url.query.get("sslmode", "verify-full")
            if mode not in {"require", "verify-full"}:
                raise RuntimeError("PostgreSQL remoto exige TLS com verificação de certificado.")
            url = url.update_query_dict({"sslmode": "verify-full", "sslrootcert": certifi.where()})
        return url
    if url.drivername != "sqlite":
        raise RuntimeError("Apenas SQLite local e PostgreSQL/psycopg são suportados.")
    return url


def migration_url():
    application = database_url()
    direct = value("DATABASE_MIGRATION_URL")
    if application.get_backend_name() == "postgresql":
        if not direct:
            raise RuntimeError("Defina DATABASE_MIGRATION_URL direta no painel privado.")
        url = database_url(direct)
        if url.get_backend_name() != "postgresql" or "-pooler" in (url.host or ""):
            raise RuntimeError("As migrações PostgreSQL exigem uma ligação direta.")
        if application.database != url.database or (application.host or "").replace("-pooler", "") != (url.host or ""):
            raise RuntimeError("A ligação direta deve corresponder à mesma base e endpoint da aplicação.")
        return url
    return database_url(direct) if direct else application


def build_engine(url, migration=False):
    args = {"pool_pre_ping": True, "hide_parameters": True}
    if url.get_backend_name() == "sqlite":
        args["connect_args"] = {"check_same_thread": False, "timeout": 20}
    else:
        args["connect_args"] = {"connect_timeout": 15, "prepare_threshold": None}
        if migration:
            args["poolclass"] = NullPool
        else:
            args.update(pool_size=2, max_overflow=2, pool_timeout=20, pool_recycle=300)
    return create_engine(url, **args)
