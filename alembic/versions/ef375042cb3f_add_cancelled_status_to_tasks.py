"""Add cancelled status to tasks

Revision ID: ef375042cb3f
Revises: 161422f1d9c0
Create Date: 2023-05-22 21:11:46.494408

"""
from alembic import op
import sqlalchemy as sa

task_status_type = sa.Enum(
    'pending_approval',
    'on_hold',
    'in_progress',
    'finished',
    'rejected',
    'cancelled',
    name='task_status'
)

# revision identifiers, used by Alembic.
revision = 'ef375042cb3f'
down_revision = 'bb56f0eca8c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('tasks', 'status', type_=task_status_type)
    op.add_column('tasks', sa.Column('cancellation_reason', sa.String(150)))


def downgrade() -> None:
    op.drop_column('tasks', 'cancellation_reason')
