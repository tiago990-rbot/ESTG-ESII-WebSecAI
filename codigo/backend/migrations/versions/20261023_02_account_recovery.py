"""Add single-use account links and revocable sessions without replacing data."""
from alembic import op
import sqlalchemy as sa
from app.models.account_action import AccountAction

revision = "20261023_02"
down_revision = "20261021_01"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    if "auth_version" not in columns:
        op.add_column("users", sa.Column("auth_version", sa.Integer(), nullable=False, server_default=sa.text("0")))
    if "password_ready" not in columns:
        op.add_column("users", sa.Column("password_ready", sa.Boolean(), nullable=False, server_default=sa.true()))
    AccountAction.__table__.create(bind=bind, checkfirst=True)


def downgrade():
    raise RuntimeError("Downgrade destrutivo nao suportado. Rever rollback com a versao de autenticacao atual.")
