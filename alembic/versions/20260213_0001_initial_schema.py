"""Initial schema.

Revision ID: 20260213_0001
Revises:
Create Date: 2026-02-13 08:30:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260213_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "counterparties",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("contact_info", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_counterparties_id"), "counterparties", ["id"], unique=False)
    op.create_index(op.f("ix_counterparties_name"), "counterparties", ["name"], unique=True)

    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("income", sa.Float(), nullable=False),
        sa.Column("expense", sa.Float(), nullable=False),
        sa.Column("tax", sa.Float(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("counterparty_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["counterparty_id"], ["counterparties.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_counterparty_id"), "transactions", ["counterparty_id"], unique=False)
    op.create_index(op.f("ix_transactions_date"), "transactions", ["date"], unique=False)
    op.create_index(op.f("ix_transactions_id"), "transactions", ["id"], unique=False)

    # Keep parity with custom indexes created in models.py after_create hook.
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_date_desc "
        "ON transactions(date DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_counterparty_date "
        "ON transactions(counterparty_id, date DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_income "
        "ON transactions(income)"
    )


def downgrade() -> None:
    op.drop_index("idx_transactions_income", table_name="transactions")
    op.drop_index("idx_transactions_counterparty_date", table_name="transactions")
    op.drop_index("idx_transactions_date_desc", table_name="transactions")

    op.drop_index(op.f("ix_transactions_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_date"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_counterparty_id"), table_name="transactions")
    op.drop_table("transactions")

    op.drop_index(op.f("ix_counterparties_name"), table_name="counterparties")
    op.drop_index(op.f("ix_counterparties_id"), table_name="counterparties")
    op.drop_table("counterparties")

