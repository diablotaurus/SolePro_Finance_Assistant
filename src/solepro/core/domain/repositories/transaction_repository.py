"""
Интерфейс репозитория для работы с транзакциями.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ..entities.transaction import Transaction


@dataclass(frozen=True)
class TransactionView:
    """
    Read-model: транзакция вместе с уже загруженным именем контрагента.

    Используется на read-путях (список, поиск, статистика), чтобы отдавать
    имя контрагента без дополнительных запросов к БД (оно уже загружается
    тем же JOIN, что и сама транзакция).
    """
    transaction: Transaction
    counterparty_name: Optional[str] = None


class TransactionRepository(ABC):
    """
    Абстрактный репозиторий для работы с транзакциями.
    
    Этот интерфейс определяет контракт для всех реализаций репозитория.
    Доменный слой зависит только от этого интерфейса, а не от конкретной реализации.
    """
    
    @abstractmethod
    def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """
        Найти транзакцию по ID.
        
        Args:
            transaction_id: ID транзакции
            
        Returns:
            Транзакция или None если не найдена
        """
        pass
    
    @abstractmethod
    def save(self, transaction: Transaction) -> Transaction:
        """
        Сохранить транзакцию.
        
        Args:
            transaction: Транзакция для сохранения
            
        Returns:
            Сохраненная транзакция (с обновленным ID если необходимо)
        """
        pass
    
    @abstractmethod
    def delete(self, transaction_id: UUID) -> bool:
        """
        Удалить транзакцию.
        
        Args:
            transaction_id: ID транзакции для удаления
            
        Returns:
            True если удалена, False если не найдена
        """
        pass
    
    @abstractmethod
    def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "date_desc"
    ) -> List[Transaction]:
        """
        Найти все транзакции с пагинацией.
        
        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            order_by: Поле и направление сортировки
            
        Returns:
            Список транзакций
        """
        pass
    
    @abstractmethod
    def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """
        Найти транзакции за период.
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список транзакций за период
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query: str,
        fields: List[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """
        Поиск транзакций по тексту.
        
        Args:
            query: Текст для поиска
            fields: Поля для поиска (если None, искать во всех полях)
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список найденных транзакций
        """
        pass
    
    @abstractmethod
    def get_by_id_with_counterparty(
        self, transaction_id: UUID
    ) -> Optional[TransactionView]:
        """
        Найти транзакцию по ID вместе с именем контрагента (read-model).

        Args:
            transaction_id: ID транзакции

        Returns:
            TransactionView или None если не найдена
        """
        pass

    @abstractmethod
    def find_all_with_counterparty(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "date_desc"
    ) -> List[TransactionView]:
        """
        Найти все транзакции вместе с именами контрагентов (read-model).

        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            order_by: Поле и направление сортировки

        Returns:
            Список read-моделей транзакций
        """
        pass

    @abstractmethod
    def search_with_counterparty(
        self,
        query: str,
        fields: List[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransactionView]:
        """
        Поиск транзакций вместе с именами контрагентов (read-model).

        Args:
            query: Текст для поиска
            fields: Поля для поиска (если None, искать во всех полях)
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Список read-моделей найденных транзакций
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Получить общее количество транзакций.
        
        Returns:
            Количество транзакций
        """
        pass
    
    @abstractmethod
    def exists(self, transaction_id: UUID) -> bool:
        """
        Проверить существование транзакции.
        
        Args:
            transaction_id: ID транзакции
            
        Returns:
            True если существует
        """
        pass

    @abstractmethod
    def commit(self) -> None:
        """Apply pending transaction changes."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback pending transaction changes."""
        pass
