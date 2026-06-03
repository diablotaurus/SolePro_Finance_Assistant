"""
Интерфейс репозитория для работы с контрагентами.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..entities.counterparty import Counterparty


class CounterpartyRepository(ABC):
    """
    Абстрактный репозиторий для работы с контрагентами.
    
    Этот интерфейс определяет контракт для всех реализаций репозитория.
    Доменный слой зависит только от этого интерфейса, а не от конкретной реализации.
    """
    
    @abstractmethod
    def get_by_id(self, counterparty_id: UUID) -> Optional[Counterparty]:
        """
        Найти контрагента по ID.
        
        Args:
            counterparty_id: ID контрагента
            
        Returns:
            Контрагент или None если не найден
        """
        pass
    
    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Counterparty]:
        """
        Найти контрагента по имени.
        
        Args:
            name: Имя контрагента
            
        Returns:
            Контрагент или None если не найден
        """
        pass
    
    @abstractmethod
    def save(self, counterparty: Counterparty) -> Counterparty:
        """
        Сохранить контрагента.
        
        Args:
            counterparty: Контрагент для сохранения
            
        Returns:
            Сохраненный контрагент (с обновленным ID если необходимо)
        """
        pass
    
    @abstractmethod
    def delete(self, counterparty_id: UUID) -> bool:
        """
        Удалить контрагента.
        
        Args:
            counterparty_id: ID контрагента для удаления
            
        Returns:
            True если удален, False если не найден
        """
        pass
    
    @abstractmethod
    def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "name_asc"
    ) -> List[Counterparty]:
        """
        Найти всех контрагентов с пагинацией.
        
        Args:
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            order_by: Поле и направление сортировки
            
        Returns:
            Список контрагентов
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query: str,
        fields: List[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Counterparty]:
        """
        Поиск контрагентов по тексту.
        
        Args:
            query: Текст для поиска
            fields: Поля для поиска (если None, искать во всех полях)
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            
        Returns:
            Список найденных контрагентов
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику по контрагентам.
        
        Returns:
            Словарь со статистикой
        """
        pass

    @abstractmethod
    def get_transaction_aggregates(
        self,
        counterparty_ids: List[UUID]
    ) -> Dict[UUID, Dict[str, Any]]:
        """
        Получить агрегаты по транзакциям для списка контрагентов.

        Args:
            counterparty_ids: Список ID контрагентов

        Returns:
            Словарь вида {counterparty_id: {"transaction_count": int, "total_income": Decimal}}
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """
        Получить общее количество контрагентов.
        
        Returns:
            Количество контрагентов
        """
        pass
    
    @abstractmethod
    def exists(self, counterparty_id: UUID) -> bool:
        """
        Проверить существование контрагента по ID.
        
        Args:
            counterparty_id: ID контрагента
            
        Returns:
            True если существует
        """
        pass
    
    @abstractmethod
    def exists_by_name(self, name: str) -> bool:
        """
        Проверить существование контрагента по имени.
        
        Args:
            name: Имя контрагента
            
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
