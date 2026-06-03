"""Switch transaction money columns from Float to Numeric(14, 2).

Revision ID: 20260214_0002
Revises: 20260213_0001
Create Date: 2026-02-14 20:10:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260214_0002"
down_revision: Union[str, Sequence[str], None] = "20260213_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _numeric_type() -> sa.Numeric:
    return sa.Numeric(14, 2)


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        with op.batch_alter_table("transactions", recreate="always") as batch_op:
            batch_op.alter_column(
                "income",
                existing_type=sa.Float(),
                type_=_numeric_type(),
                existing_nullable=False,
            )
            batch_op.alter_column(
                "expense",
                existing_type=sa.Float(),
                type_=_numeric_type(),
                existing_nullable=False,
            )
            batch_op.alter_column(
                "tax",
                existing_type=sa.Float(),
                type_=_numeric_type(),
                existing_nullable=False,
            )
        return

    op.alter_column(
        "transactions",
        "income",
        existing_type=sa.Float(),
        type_=_numeric_type(),
        existing_nullable=False,
        postgresql_using="income::numeric(14,2)",
    )
    op.alter_column(
        "transactions",
        "expense",
        existing_type=sa.Float(),
        type_=_numeric_type(),
        existing_nullable=False,
        postgresql_using="expense::numeric(14,2)",
    )
    op.alter_column(
        "transactions",
        "tax",
        existing_type=sa.Float(),
        type_=_numeric_type(),
        existing_nullable=False,
        postgresql_using="tax::numeric(14,2)",
    )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        with op.batch_alter_table("transactions", recreate="always") as batch_op:
            batch_op.alter_column(
                "income",
                existing_type=_numeric_type(),
                type_=sa.Float(),
                existing_nullable=False,
            )
            batch_op.alter_column(
                "expense",
                existing_type=_numeric_type(),
                type_=sa.Float(),
                existing_nullable=False,
            )
            batch_op.alter_column(
                "tax",
                existing_type=_numeric_type(),
                type_=sa.Float(),
                existing_nullable=False,
            )
        return

    op.alter_column(
        "transactions",
        "income",
        existing_type=_numeric_type(),
        type_=sa.Float(),
        existing_nullable=False,
        postgresql_using="income::double precision",
    )
    op.alter_column(
        "transactions",
        "expense",
        existing_type=_numeric_type(),
        type_=sa.Float(),
        existing_nullable=False,
        postgresql_using="expense::double precision",
    )
    op.alter_column(
        "transactions",
        "tax",
        existing_type=_numeric_type(),
        type_=sa.Float(),
        existing_nullable=False,
        postgresql_using="tax::double precision",
    )
