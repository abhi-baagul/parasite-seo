"""Revision 0010 — User profile fields and workspace notifications."""

from alembic import op

revision = "0010_user_profile_notifications"
down_revision = "0009_auto_backlink_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(80)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS organization VARCHAR(200)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS job_title VARCHAR(120)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS website VARCHAR(2048)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT")
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS notification_prefs JSONB NOT NULL DEFAULT '{}'::jsonb"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
            source_key VARCHAR(180) NOT NULL,
            kind VARCHAR(32) NOT NULL DEFAULT 'info',
            title VARCHAR(300) NOT NULL,
            body TEXT NOT NULL,
            href VARCHAR(500),
            is_read BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_notifications_user_source UNIQUE (user_id, source_key)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_is_read ON notifications (is_read)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications (created_at)")


def downgrade() -> None:
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_column("users", "notification_prefs")
    op.drop_column("users", "bio")
    op.drop_column("users", "website")
    op.drop_column("users", "job_title")
    op.drop_column("users", "organization")
    op.drop_column("users", "timezone")
