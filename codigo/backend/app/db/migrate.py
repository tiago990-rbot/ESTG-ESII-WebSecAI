from alembic import command
from alembic.config import Config
from app.core.config import ROOT

def upgrade_schema():
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
