"""make source_resource_id nullable for external references

Revision ID: 820997f91dcb
Revises: ea60b8e7bbfc
Create Date: 2025-05-31 17:46:22.387815

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '820997f91dcb'
down_revision = 'ea60b8e7bbfc'
branch_labels = None
depends_on = None


def upgrade():
    # Make source_resource_id nullable for external references
    op.alter_column('kubernetesresourcereference', 'source_resource_id',
                   existing_type=sa.UUID(),
                   nullable=True)


def downgrade():
    # Make source_resource_id not nullable again
    # Note: This might fail if there are NULL values in the column
    op.alter_column('kubernetesresourcereference', 'source_resource_id',
                   existing_type=sa.UUID(),
                   nullable=False)
