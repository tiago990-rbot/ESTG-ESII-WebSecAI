"""Append-only human review trail; no change to existing evidence or accounts."""
from alembic import op
from app.models.investigation import EvidenceReview
revision = "20261024_03"
down_revision = "20261023_02"
branch_labels = None
depends_on = None

def upgrade():
    EvidenceReview.__table__.create(bind=op.get_bind(), checkfirst=True)

def downgrade():
    raise RuntimeError("O histórico de revisão é preservado; rollback por versão do código, sem remover a tabela.")
