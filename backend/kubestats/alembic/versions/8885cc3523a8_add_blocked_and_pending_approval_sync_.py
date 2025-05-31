"""add_blocked_and_pending_approval_sync_statuses

Revision ID: 8885cc3523a8
Revises: da5d1e860c14
Create Date: 2025-05-31 23:01:19.649218

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '8885cc3523a8'
down_revision = 'da5d1e860c14'
branch_labels = None
depends_on = None


def upgrade():
    # Add new values to the syncstatus enum
    op.execute("ALTER TYPE syncstatus ADD VALUE 'BLOCKED'")
    op.execute("ALTER TYPE syncstatus ADD VALUE 'PENDING_APPROVAL'")


def downgrade():
    # Note: PostgreSQL doesn't support removing enum values, so we recreate the enum
    # First, update any BLOCKED or PENDING_APPROVAL status back to PENDING
    op.execute("UPDATE repository SET sync_status = 'PENDING' WHERE sync_status IN ('BLOCKED', 'PENDING_APPROVAL')")
    op.execute("UPDATE repository SET scan_status = 'PENDING' WHERE scan_status IN ('BLOCKED', 'PENDING_APPROVAL')")
    
    # Create new enum without the new values
    op.execute("ALTER TYPE syncstatus RENAME TO syncstatus_old")
    op.execute("CREATE TYPE syncstatus AS ENUM ('PENDING', 'SYNCING', 'SUCCESS', 'ERROR')")
    
    # Update columns to use new enum
    op.execute("ALTER TABLE repository ALTER COLUMN sync_status TYPE syncstatus USING sync_status::text::syncstatus")
    op.execute("ALTER TABLE repository ALTER COLUMN scan_status TYPE syncstatus USING scan_status::text::syncstatus")
    
    # Drop old enum
    op.execute("DROP TYPE syncstatus_old")
