"""create tasks table

Revision ID: b45f388692dc
Revises: a4a5b53fb397
Create Date: 2023-04-02 18:23:44.099755

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b45f388692dc'
down_revision = 'a4a5b53fb397'
branch_labels = None
depends_on = None

task_status_type = sa.Enum(
    'pending_approval',
    'on_hold',
    'in_progress',
    'finished',
    'rejected',
    name='task_status'
)


def upgrade() -> None:
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('approved_at', sa.DateTime),
        sa.Column('rejected_at', sa.DateTime),
        sa.Column('finished_at', sa.DateTime),
        sa.Column('status', task_status_type, nullable=False),
        sa.Column('priority', sa.Integer, nullable=False)
    )


def downgrade() -> None:
    op.drop_table('tasks')
