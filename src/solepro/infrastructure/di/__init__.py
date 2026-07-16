"""
Dependency Injection контейнер.

Обеспечивает управление зависимостями и их инъекцию в компоненты приложения.
"""

from dependency_injector import containers, providers

from ..database.session_manager import DatabaseSessionManager
from ..database.unit_of_work import SQLAlchemyUnitOfWork
from ...core.application.use_cases import (
    AddTransactionUseCase,
    UpdateTransactionUseCase,
    DeleteTransactionUseCase,
    GetTransactionUseCase,
    ListTransactionsUseCase,
    SearchTransactionsUseCase,
    GetTransactionStatisticsUseCase,
    AddCounterpartyUseCase,
    UpdateCounterpartyUseCase,
    DeleteCounterpartyUseCase,
    GetCounterpartyUseCase,
    ListCounterpartiesUseCase,
    SearchCounterpartiesUseCase,
    GetCounterpartyStatisticsUseCase,
)


class Container(containers.DeclarativeContainer):
    """
    Контейнер для управления зависимостями.
    
    Использует dependency-injector для внедрения зависимостей.
    """
    
    # Менеджер сессий БД. URL берётся из конфигурации приложения (.env)
    # внутри самого DatabaseSessionManager.
    session_manager = providers.Singleton(DatabaseSessionManager)

    # Unit of Work
    unit_of_work = providers.Factory(
        SQLAlchemyUnitOfWork,
        session_manager=session_manager,
    )
    
    # Use Cases для транзакций
    add_transaction_use_case = providers.Factory(
        AddTransactionUseCase,
        unit_of_work=unit_of_work,
    )
    
    update_transaction_use_case = providers.Factory(
        UpdateTransactionUseCase,
        unit_of_work=unit_of_work,
    )
    
    delete_transaction_use_case = providers.Factory(
        DeleteTransactionUseCase,
        unit_of_work=unit_of_work,
    )
    
    get_transaction_use_case = providers.Factory(
        GetTransactionUseCase,
        unit_of_work=unit_of_work,
    )
    
    list_transactions_use_case = providers.Factory(
        ListTransactionsUseCase,
        unit_of_work=unit_of_work,
    )
    
    search_transactions_use_case = providers.Factory(
        SearchTransactionsUseCase,
        unit_of_work=unit_of_work,
    )
    
    get_transaction_statistics_use_case = providers.Factory(
        GetTransactionStatisticsUseCase,
        unit_of_work=unit_of_work,
    )
    
    # Use Cases для контрагентов
    add_counterparty_use_case = providers.Factory(
        AddCounterpartyUseCase,
        unit_of_work=unit_of_work,
    )
    
    update_counterparty_use_case = providers.Factory(
        UpdateCounterpartyUseCase,
        unit_of_work=unit_of_work,
    )
    
    delete_counterparty_use_case = providers.Factory(
        DeleteCounterpartyUseCase,
        unit_of_work=unit_of_work,
    )
    
    get_counterparty_use_case = providers.Factory(
        GetCounterpartyUseCase,
        unit_of_work=unit_of_work,
    )
    
    list_counterparties_use_case = providers.Factory(
        ListCounterpartiesUseCase,
        unit_of_work=unit_of_work,
    )
    
    search_counterparties_use_case = providers.Factory(
        SearchCounterpartiesUseCase,
        unit_of_work=unit_of_work,
    )
    
    get_counterparty_statistics_use_case = providers.Factory(
        GetCounterpartyStatisticsUseCase,
        unit_of_work=unit_of_work,
    )


# Глобальный контейнер
container = Container()
