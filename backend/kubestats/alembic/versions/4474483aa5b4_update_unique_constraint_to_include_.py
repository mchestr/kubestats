"""update_unique_constraint_to_include_file_path

Revision ID: 4474483aa5b4
Revises: a431674157c5
Create Date: 2025-06-01 13:55:06.844669

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '4474483aa5b4'
down_revision = 'a431674157c5'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the old unique constraint
    op.drop_constraint('uq_kubernetes_resource_per_repo', 'kubernetesresource', type_='unique')
    
    # Create new unique constraint that includes file_path
    op.create_unique_constraint(
        'uq_kubernetes_resource_per_repo',
        'kubernetesresource',
        ['repository_id', 'api_version', 'kind', 'name', 'namespace', 'file_path']
    )


def downgrade():
    # Drop the new unique constraint
    op.drop_constraint('uq_kubernetes_resource_per_repo', 'kubernetesresource', type_='unique')
    
    # Recreate the old unique constraint without file_path
    op.create_unique_constraint(
        'uq_kubernetes_resource_per_repo',
        'kubernetesresource',
        ['repository_id', 'api_version', 'kind', 'name', 'namespace']
    )
