"""Excel export service for desktop transactions."""

from __future__ import annotations

from typing import Protocol, Sequence

from ....core.application.dto.transaction_dto import TransactionResponseDTO


class TransactionExportServiceProtocol(Protocol):
    """Contract for transaction export service used by controller."""

    def export_to_excel(
        self,
        transactions: Sequence[TransactionResponseDTO],
        filepath: str,
    ) -> None: ...


class TransactionExportService:
    """Handles transaction export to Excel."""

    def export_to_excel(
        self,
        transactions: Sequence[TransactionResponseDTO],
        filepath: str,
    ) -> None:
        import pandas as pd

        rows = []
        for transaction in transactions:
            rows.append(
                {
                    "Дата": transaction.date.strftime("%d.%m.%Y"),
                    "Доход": float(transaction.income),
                    "Расход": float(transaction.expense),
                    "Налог": float(transaction.tax),
                    "Прибыль": float(transaction.profit),
                    "Контрагент": transaction.counterparty_name or "",
                    "Примечание": transaction.note or "",
                }
            )

        df = pd.DataFrame(rows)
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            sheet_name = "Транзакции"
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            worksheet = writer.sheets[sheet_name]
            for i, column in enumerate(df.columns, 1):
                max_len = df[column].astype(str).map(len).max() if len(df.index) else 0
                column_width = max(max_len, len(column)) + 2
                worksheet.column_dimensions[chr(64 + i)].width = min(column_width, 50)
