"""
Telegram bot handlers.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from datetime import datetime
import logging
from typing import Any, Callable, Optional

from telegram import Update
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from ...core.application.dto.transaction_dto import TransactionCreateDTO
from ...infrastructure.config import get_app_config


DATE, INCOME, EXPENSE, TAX, COUNTERPARTY, NOTE, CONFIRM = range(7)

MAIN_MENU = ReplyKeyboardMarkup([["Добавить", "Статистика"]], resize_keyboard=True)
logger = logging.getLogger(__name__)


async def _reply_internal_error(update: Update, operation: str, exc: Exception) -> None:
    """Log technical details and return a stable user-facing error message."""
    logger.error(
        "Ошибка Telegram-команды (%s): %s",
        operation,
        exc,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    if update.message:
        await update.message.reply_text(
            f"❌ Не удалось выполнить операцию «{operation}». Попробуйте позже.",
            reply_markup=MAIN_MENU,
        )


@dataclass(frozen=True)
class HandlerDependencies:
    get_transaction_statistics_use_case: Callable[[], Any]
    list_counterparties_use_case: Callable[[], Any]
    add_transaction_use_case: Callable[[], Any]
    list_transactions_use_case: Optional[Callable[[], Any]] = None
    search_transactions_use_case: Optional[Callable[[], Any]] = None
    get_counterparty_statistics_use_case: Optional[Callable[[], Any]] = None


def _default_dependencies() -> HandlerDependencies:
    from ...infrastructure.di import container

    return HandlerDependencies(
        get_transaction_statistics_use_case=container.get_transaction_statistics_use_case,
        list_counterparties_use_case=container.list_counterparties_use_case,
        add_transaction_use_case=container.add_transaction_use_case,
        list_transactions_use_case=container.list_transactions_use_case,
        search_transactions_use_case=container.search_transactions_use_case,
        get_counterparty_statistics_use_case=container.get_counterparty_statistics_use_case,
    )


_dependencies: Optional[HandlerDependencies] = None


def _get_dependencies() -> HandlerDependencies:
    global _dependencies
    if _dependencies is None:
        _dependencies = _default_dependencies()
    return _dependencies


def configure_dependencies(dependencies: Optional[HandlerDependencies]) -> None:
    global _dependencies
    _dependencies = dependencies


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "SolePro bot is running. Use /help for commands.",
            reply_markup=MAIN_MENU
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "📋 Как пользоваться ботом:\n"
            "━━━━━━━━━━━━━━━━\n"
            "1. Для добавления операции используйте /add\n"
            "2. Вводите данные по запросу бота\n"
            "3. Формат даты: ДД.ММ.ГГГГ (например: 09.01.2026 или нажмите кнопку \"Сегодня\")\n"
            "4. Суммы указывайте в рублях\n"
            "5. Для отмены введите /cancel в любой момент\n\n"
            "📊 Основные команды:\n"
            "━━━━━━━━━━━━━━━━\n"
            "/add - добавить операцию\n"
            "/stats - показать статистику\n"
            "/counterparties - список контрагентов\n"
            "/transactions - последние транзакции\n"
            "/search <текст> - поиск транзакций\n"
            "/topcounterparties - топ контрагентов"
            ,
            reply_markup=MAIN_MENU
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        use_case = _get_dependencies().get_transaction_statistics_use_case()
        stats = use_case.execute()
        first_date = stats.first_transaction_date.strftime("%d.%m.%Y") if stats.first_transaction_date else "N/A"
        last_date = stats.last_transaction_date.strftime("%d.%m.%Y") if stats.last_transaction_date else "N/A"
        await update.message.reply_text(
            "📊 Общая статистика\n"
            f"Транзакции: {stats.total_transactions}\n"
            f"Доход: {stats.total_income}\n"
            f"Расход: {stats.total_expense}\n"
            f"Налог: {stats.total_tax}\n"
            f"Прибыль: {stats.total_profit}\n"
            f"Период: {first_date} — {last_date}",
            reply_markup=MAIN_MENU
        )
    except Exception as exc:
        await _reply_internal_error(update, "получение статистики", exc)


async def counterparties_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        use_case = _get_dependencies().list_counterparties_use_case()
        result = use_case.execute(skip=0, limit=50)
        if not result.counterparties:
            await update.message.reply_text("Контрагенты не найдены.", reply_markup=MAIN_MENU)
            return
        names = [c.name for c in result.counterparties]
        await update.message.reply_text(
            "Контрагенты:\n" + "\n".join(names),
            reply_markup=MAIN_MENU
        )
    except Exception as exc:
        await _reply_internal_error(update, "получение контрагентов", exc)


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        date_format = get_app_config().date_format
        keyboard = ReplyKeyboardMarkup([["Сегодня"]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            "Введите дату транзакции.\n"
            f"Формат: {date_format} (например, 08.02.2026). "
            "Можно написать 'сегодня'.",
            reply_markup=keyboard
        )
    return DATE


def _parse_decimal(value: str) -> Decimal:
    normalized = value.replace(",", ".").strip()
    return Decimal(normalized)


async def add_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return DATE
    text = update.message.text.strip().lower()
    if text in {"today", "сегодня"}:
        context.user_data["date"] = datetime.now()
    else:
        date_format = get_app_config().date_format
        try:
            parsed = datetime.strptime(update.message.text.strip(), date_format)
            if parsed.date() == datetime.now().date():
                parsed = datetime.now()
            context.user_data["date"] = parsed
        except ValueError:
            await update.message.reply_text(f"Неверная дата. Формат: {date_format}.")
            return DATE
    await update.message.reply_text("Введите доход (число, можно 0).", reply_markup=ReplyKeyboardRemove())
    return INCOME


async def add_income(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return INCOME
    try:
        value = _parse_decimal(update.message.text)
        if value < 0:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        await update.message.reply_text("Неверная сумма. Введите число >= 0.")
        return INCOME
    context.user_data["income"] = value
    await update.message.reply_text("Введите расход (число, можно 0).")
    return EXPENSE


async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return EXPENSE
    try:
        value = _parse_decimal(update.message.text)
        if value < 0:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        await update.message.reply_text("Неверная сумма. Введите число >= 0.")
        return EXPENSE
    context.user_data["expense"] = value
    await update.message.reply_text("Введите налог (число, можно 0).")
    return TAX


async def add_tax(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return TAX
    try:
        value = _parse_decimal(update.message.text)
        if value < 0:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        await update.message.reply_text("Неверная сумма. Введите число >= 0.")
        return TAX
    context.user_data["tax"] = value
    keyboard_rows = []
    try:
        use_case = _get_dependencies().list_counterparties_use_case()
        result = use_case.execute(skip=0, limit=10)
        names = [c.name for c in result.counterparties]
        for i in range(0, len(names), 2):
            keyboard_rows.append(names[i:i + 2])
    except Exception as exc:
        logger.warning(
            "Не удалось загрузить контрагентов для клавиатуры: %s",
            exc,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        keyboard_rows = []
    keyboard_rows.append(["-"])
    keyboard = ReplyKeyboardMarkup(keyboard_rows, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Введите контрагента или '-' чтобы пропустить.",
        reply_markup=keyboard
    )
    return COUNTERPARTY


async def add_counterparty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return COUNTERPARTY
    text = update.message.text.strip()
    context.user_data["counterparty_name"] = None if text in {"-", "нет", "skip"} else text
    await update.message.reply_text("Введите примечание или '-' чтобы пропустить.", reply_markup=ReplyKeyboardRemove())
    return NOTE


async def add_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return NOTE
    text = update.message.text.strip()
    context.user_data["note"] = None if text in {"-", "нет", "skip"} else text
    data = context.user_data
    date_format = get_app_config().date_format
    date_str = data["date"].strftime(date_format)
    summary = (
        "Проверьте данные:\n"
        f"Дата: {date_str}\n"
        f"Доход: {data['income']}\n"
        f"Расход: {data['expense']}\n"
        f"Налог: {data['tax']}\n"
        f"Контрагент: {data.get('counterparty_name') or '—'}\n"
        f"Примечание: {data.get('note') or '—'}\n\n"
        "Подтвердить? (да/нет)"
    )
    keyboard = ReplyKeyboardMarkup([["Да", "Нет"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(summary, reply_markup=keyboard)
    return CONFIRM


async def add_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return CONFIRM
    text = update.message.text.strip().lower()
    if text not in {"да", "yes", "y", "ok"}:
        await update.message.reply_text("Создание отменено. /add чтобы начать снова.", reply_markup=MAIN_MENU)
        context.user_data.clear()
        return ConversationHandler.END
    data = context.user_data
    try:
        dto = TransactionCreateDTO(
            date=data["date"],
            income=data["income"],
            expense=data["expense"],
            tax=data["tax"],
            counterparty_name=data.get("counterparty_name"),
            note=data.get("note"),
        )
        use_case = _get_dependencies().add_transaction_use_case()
        transaction = use_case.execute(dto)
        await update.message.reply_text(
            "✅ Транзакция добавлена:\n"
            f"ID: {transaction.id}\n"
            f"Дата: {transaction.date.strftime(get_app_config().date_format)}\n"
            f"Прибыль: {transaction.profit}\n"
            f"Контрагент: {transaction.counterparty_name or '—'}",
            reply_markup=MAIN_MENU
        )
    except Exception as exc:
        await _reply_internal_error(update, "добавление транзакции", exc)
    finally:
        context.user_data.clear()
    return ConversationHandler.END


async def add_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message:
        await update.message.reply_text("Создание отменено. /add чтобы начать снова.", reply_markup=MAIN_MENU)
    context.user_data.clear()
    return ConversationHandler.END


def _format_transaction_line(transaction: Any) -> str:
    date_str = transaction.date.strftime(get_app_config().date_format)
    counterparty = transaction.counterparty_name or "—"
    line = (
        f"🗓 {date_str} | "
        f"Дох: {transaction.income} Расх: {transaction.expense} Налог: {transaction.tax} | "
        f"Приб: {transaction.profit} | {counterparty}"
    )
    note = (transaction.note or "").strip()
    if note:
        line += f" | {note}"
    return line


async def transactions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        use_case = _get_dependencies().list_transactions_use_case()
        result = use_case.execute(skip=0, limit=10, order_by="date_desc")
        if not result.transactions:
            await update.message.reply_text("Транзакции не найдены.", reply_markup=MAIN_MENU)
            return
        lines = [_format_transaction_line(tx) for tx in result.transactions]
        header = f"📋 Последние транзакции ({len(result.transactions)} из {result.total_count}):"
        await update.message.reply_text(
            header + "\n" + "\n".join(lines),
            reply_markup=MAIN_MENU
        )
    except Exception as exc:
        await _reply_internal_error(update, "получение транзакций", exc)


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    args = getattr(context, "args", None) or []
    query = " ".join(args).strip()
    if not query:
        await update.message.reply_text(
            "Использование: /search <текст>\nНапример: /search аренда",
            reply_markup=MAIN_MENU
        )
        return
    try:
        use_case = _get_dependencies().search_transactions_use_case()
        result = use_case.execute(query=query, limit=10)
        if not result.transactions:
            await update.message.reply_text(
                f"По запросу «{query}» ничего не найдено.",
                reply_markup=MAIN_MENU
            )
            return
        lines = [_format_transaction_line(tx) for tx in result.transactions]
        header = f"🔎 Результаты поиска «{query}» ({len(result.transactions)} из {result.total_count}):"
        await update.message.reply_text(
            header + "\n" + "\n".join(lines),
            reply_markup=MAIN_MENU
        )
    except Exception as exc:
        await _reply_internal_error(update, "поиск транзакций", exc)


async def topcounterparties_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    try:
        use_case = _get_dependencies().get_counterparty_statistics_use_case()
        stats = use_case.execute()
        if not stats:
            await update.message.reply_text(
                "Статистика по контрагентам недоступна.",
                reply_markup=MAIN_MENU
            )
            return
        lines = []
        for index, item in enumerate(stats[:10], start=1):
            lines.append(
                f"{index}. {item.counterparty_name} — "
                f"доход {item.total_income}, прибыль {item.total_profit}, "
                f"операций {item.transaction_count} ({item.percentage_of_total:.1f}%)"
            )
        await update.message.reply_text(
            "🏆 Топ контрагентов:\n" + "\n".join(lines),
            reply_markup=MAIN_MENU
        )
    except Exception as exc:
        await _reply_internal_error(update, "статистика по контрагентам", exc)


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("Unknown command. Use /help.")


def setup_handlers(
    application: Application,
    dependencies: Optional[HandlerDependencies] = None
) -> None:
    if dependencies is not None:
        configure_dependencies(dependencies)

    add_conv = ConversationHandler(
        entry_points=[
            CommandHandler("add", add_command),
            MessageHandler(filters.Regex("^Добавить$"), add_command),
        ],
        states={
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_date)],
            INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_income)],
            EXPENSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense)],
            TAX: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_tax)],
            COUNTERPARTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_counterparty)],
            NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_note)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_confirm)],
        },
        fallbacks=[CommandHandler("cancel", add_cancel)],
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("stat", stats_command))
    application.add_handler(CommandHandler("counterparties", counterparties_command))
    application.add_handler(CommandHandler("transactions", transactions_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("topcounterparties", topcounterparties_command))
    application.add_handler(MessageHandler(filters.Regex("^Статистика$"), stats_command))
    application.add_handler(add_conv)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
