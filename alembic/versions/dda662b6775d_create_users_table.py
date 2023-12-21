"""create users table

Revision ID: dda662b6775d
Revises:
Create Date: 2023-04-01 22:27:11.119142

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


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
        sa.Column('password', sa.String(150), nullable=False)
    )

    # To avoid trying to create type 'role' again after downgrading
    # https://github.com/sqlalchemy/alembic/issues/278#issuecomment-819209060
    user_role = postgresql.ENUM('user', 'admin', name='role', create_type=False)
    user_role.create(op.get_bind(), checkfirst=True)
    op.add_column('users', sa.Column('role', user_role, nullable=False))


def downgrade() -> None:
    op.drop_table('users')
