from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from app.db.configuration import database_url, build_engine
DATABASE_URL = database_url()
engine = build_engine(DATABASE_URL)
if DATABASE_URL.get_backend_name() == "sqlite":
    @event.listens_for(engine, "connect")
    def sqlite_settings(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=20000")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    with SessionLocal() as db:
        yield db
