"""Add quota audit and safe provider observations; preserve existing counters."""
from alembic import op
from app.models.quota import QuotaGrant, ProviderObservation
revision = "20261030_04"
down_revision = "20261024_03"
branch_labels = depends_on = None

def upgrade():
    for table in (QuotaGrant.__table__, ProviderObservation.__table__):
        table.create(bind=op.get_bind(), checkfirst=True)

def downgrade():
    raise RuntimeError("Preservar auditoria e contadores. Reverter código sem apagar tabelas.")
