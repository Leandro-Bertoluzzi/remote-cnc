"""create files table

Revision ID: a4a5b53fb397
Revises: dda662b6775d
Create Date: 2023-04-02 18:03:14.045945

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = 'a4a5b53fb397'
down_revision = 'dda662b6775d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'files',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer),
        sa.Column('file_name', sa.String(150), nullable=False),
        sa.Column('file_path', sa.String(150), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=func.now()),
    )
    op.create_foreign_key(
        "fk_user_id",
        "files",
        "users",
        ["user_id"],
        ["id"],
        ondelete='CASCADE'
    )

def downgrade() -> None:
    op.drop_table('files')
