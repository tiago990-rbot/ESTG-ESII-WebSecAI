from alembic import op
from app.models.lab import LabProject, LabRun, LabReview
revision="20261030_05"
down_revision="20261030_04"
branch_labels=depends_on=None
def upgrade():
    for table in (LabProject.__table__,LabRun.__table__,LabReview.__table__):table.create(bind=op.get_bind(),checkfirst=True)
def downgrade():
    raise RuntimeError("Preservar projetos e auditoria. Reverter apenas código.")
