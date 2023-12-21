"""create tasks table

Revision ID: b45f388692dc
Revises: a4a5b53fb397
Create Date: 2023-04-02 18:23:44.099755

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b45f388692dc'
down_revision = 'a4a5b53fb397'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('status_updated_at', sa.DateTime),
        sa.Column('priority', sa.Integer, nullable=False)
    )

    # To avoid trying to create type 'status' again after downgrading
    # https://github.com/sqlalchemy/alembic/issues/278#issuecomment-819209060
    task_status_type = postgresql.ENUM(
        'pending_approval',
        'on_hold',
        'in_progress',
        'finished',
        'rejected',
        name='task_status',
        create_type=False
    )
    task_status_type.create(op.get_bind(), checkfirst=True)
    op.add_column('tasks', sa.Column('status', task_status_type, nullable=False))


def downgrade() -> None:
    op.drop_table('tasks')
