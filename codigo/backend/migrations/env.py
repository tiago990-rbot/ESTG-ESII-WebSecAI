from alembic import context
from app.db.base import Base
from app.db.configuration import migration_url, build_engine
from app.models import user, scan, finding
from app.models import investigation, account_action

config = context.config
DATABASE_URL = migration_url()
if context.is_offline_mode():
    context.configure(url=DATABASE_URL, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = build_engine(DATABASE_URL, migration=True)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata, render_as_batch=connection.dialect.name == "sqlite")
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
