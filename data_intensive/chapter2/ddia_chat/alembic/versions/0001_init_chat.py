from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_init_chat"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "chat_room",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "room_member",
        sa.Column("room_id", sa.BigInteger(), sa.ForeignKey("chat_room.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("role", sa.String(length=16), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_room_member_user_room", "room_member", ["user_id", "room_id"])

    op.create_table(
        "room_seq",
        sa.Column("room_id", sa.BigInteger(), sa.ForeignKey("chat_room.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("last_seq", sa.BigInteger(), nullable=False, server_default="0"),
    )

    op.create_table(
        "room_summary",
        sa.Column("room_id", sa.BigInteger(), sa.ForeignKey("chat_room.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("last_message_seq", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("last_message_at", sa.DateTime(timezone=True)),
        sa.Column("last_message_preview", sa.String(length=256)),
        sa.Column("last_sender_id", sa.BigInteger()),
    )

    op.create_table(
        "room_read_state",
        sa.Column("room_id", sa.BigInteger(), sa.ForeignKey("chat_room.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("last_read_seq", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_read_state_user_room", "room_read_state", ["user_id", "room_id"])

    op.create_table(
        "message",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("room_id", sa.BigInteger(), sa.ForeignKey("chat_room.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", sa.BigInteger(), nullable=False),
        sa.Column("seq", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("edited_at", sa.DateTime(timezone=True)),
        sa.Column("deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("search_vector", postgresql.TSVECTOR()),
        sa.UniqueConstraint("room_id", "seq", name="uq_message_room_seq"),
        sa.CheckConstraint("seq > 0", name="ck_message_seq_positive"),
    )
    op.create_index("ix_message_room_seq_desc", "message", ["room_id", "seq"])
    op.create_index("ix_message_search_vector_gin", "message", ["search_vector"], postgresql_using="gin")

    op.create_table(
        "message_mention",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("message_id", sa.BigInteger(), sa.ForeignKey("message.id", ondelete="CASCADE"), nullable=False),
        sa.Column("room_id", sa.BigInteger(), nullable=False),
        sa.Column("mentioned_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_mention_user_created", "message_mention", ["mentioned_user_id", "created_at"])
    op.create_index("ix_mention_room_message", "message_mention", ["room_id", "message_id"])

    # Trigger to auto-maintain tsvector from content
    op.execute("""
    CREATE FUNCTION message_search_vector_update() RETURNS trigger AS $$
    begin
      new.search_vector :=
        to_tsvector('simple', coalesce(new.content, ''));
      return new;
    end
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE TRIGGER trg_message_search_vector
    BEFORE INSERT OR UPDATE OF content
    ON message
    FOR EACH ROW EXECUTE FUNCTION message_search_vector_update();
    """)

def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_message_search_vector ON message;")
    op.execute("DROP FUNCTION IF EXISTS message_search_vector_update;")
    op.drop_table("message_mention")
    op.drop_table("message")
    op.drop_table("room_read_state")
    op.drop_table("room_summary")
    op.drop_table("room_seq")
    op.drop_table("room_member")
    op.drop_table("chat_room")
