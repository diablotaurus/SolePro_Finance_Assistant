"""Clean up dangling counterparty references in transactions.

Before v1.4.19 deleting a counterparty left its transactions pointing to a
nonexistent row (SQLite foreign keys were not enforced, so ON DELETE SET NULL
never fired). This migration nulls out such references.

Revision ID: 20260716_0003
Revises: 20260214_0002
Create Date: 2026-07-16 12:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260716_0003"
down_revision: Union[str, Sequence[str], None] = "20260214_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE transactions SET counterparty_id = NULL "
            "WHERE counterparty_id IS NOT NULL "
            "AND counterparty_id NOT IN (SELECT id FROM counterparties)"
        )
    )


def downgrade() -> None:
    # Данные для восстановления ссылок утеряны — откат невозможен и не нужен.
    pass
