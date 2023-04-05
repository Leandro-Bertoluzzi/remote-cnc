"""create users table

Revision ID: dda662b6775d
Revises: 
Create Date: 2023-04-01 22:27:11.119142

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dda662b6775d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('email', sa.String(50), nullable=False),
        sa.Column('password', sa.String(100), nullable=False),
        sa.Column('role', sa.Enum('user', 'admin', name='role'), nullable=False)
    )

def downgrade() -> None:
    op.drop_table('users')
