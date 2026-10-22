"""Adopt the existing schema and add investigations without replacing legacy data."""
from alembic import op
from app.db.base import Base
from app.models import user, scan, finding, investigation
revision = "20261021_01"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    for table in Base.metadata.sorted_tables:
        table.create(bind=bind, checkfirst=True)

def downgrade():
    raise RuntimeError("Downgrade destrutivo não suportado. Restaure uma cópia verificada.")
