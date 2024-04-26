"""Add cancelled status to tasks

Revision ID: ef375042cb3f
Revises: 161422f1d9c0
Create Date: 2023-05-22 21:11:46.494408

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ef375042cb3f'
down_revision = 'bb56f0eca8c5'
branch_labels = None
depends_on = None


# Describing of enum
enum_name = "task_status"
temp_enum_name = f"temp_{enum_name}"
old_values = (
    "pending_approval",
    "on_hold",
    "in_progress",
    "finished",
    "rejected"
)
new_values = ("cancelled", *old_values)
old_type = sa.Enum(*old_values, name=enum_name)
new_type = sa.Enum(*new_values, name=enum_name)
temp_type = sa.Enum(*new_values, name=temp_enum_name)


# Describing of table
table_name = "tasks"
column_name = "status"


def upgrade() -> None:
    # Add column for cancellation reason
    op.add_column('tasks', sa.Column('cancellation_reason', sa.String(150)))

    # temp type to use instead of old one
    temp_type.create(op.get_bind(), checkfirst=False)

    # changing of column type from old enum to new one.
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.alter_column(
            column_name,
            existing_type=old_type,
            type_=temp_type,
            existing_nullable=False,
            postgresql_using=f"{column_name}::text::{temp_enum_name}"
        )

    # remove old enum, create new enum
    old_type.drop(op.get_bind(), checkfirst=False)
    new_type.create(op.get_bind(), checkfirst=False)

    # changing of column type from temp enum to new one.
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.alter_column(
            column_name,
            existing_type=temp_type,
            type_=new_type,
            existing_nullable=False,
            postgresql_using=f"{column_name}::text::{enum_name}"
        )

    # remove temp enum
    temp_type.drop(op.get_bind(), checkfirst=False)


def downgrade() -> None:
    # Drop column for cancellation reason
    op.drop_column('tasks', 'cancellation_reason')

    # Convert 'cancelled' status into 'rejected'
    table = sa.sql.table('tasks', sa.Column('status'))
    op.execute(
        table
        .update()
        .where(table.columns.status == 'cancelled')
        .values(status='rejected')
    )

    # Remove 'cancelled' value from type
    temp_type.create(op.get_bind(), checkfirst=False)

    with op.batch_alter_table('tasks') as batch_op:
        batch_op.alter_column(
            column_name,
            existing_type=new_type,
            type_=temp_type,
            existing_nullable=False,
            postgresql_using=f"{column_name}::text::{temp_enum_name}"
        )

    new_type.drop(op.get_bind(), checkfirst=False)
    old_type.create(op.get_bind(), checkfirst=False)

    with op.batch_alter_table('tasks') as batch_op:
        batch_op.alter_column(
            column_name,
            existing_type=temp_type,
            type_=old_type,
            existing_nullable=False,
            postgresql_using=f"{column_name}::text::{enum_name}"
        )

    temp_type.drop(op.get_bind(), checkfirst=False)
