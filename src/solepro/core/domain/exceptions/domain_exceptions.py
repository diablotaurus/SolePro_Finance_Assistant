"""
Исключения доменного слоя.
"""


class DomainException(Exception):
    """Базовое исключение доменного слоя."""
    pass


class InvalidTransactionException(DomainException):
    """Некорректная транзакция."""
    pass


class InvalidCounterpartyException(DomainException):
    """Некорректный контрагент."""
    pass


class InvalidMoneyException(DomainException):
    """Некорректная денежная сумма."""
    pass


class BusinessRuleViolationException(DomainException):
    """Нарушение бизнес-правила."""
    pass


class EntityNotFoundException(DomainException):
    """Сущность не найдена."""
    
    def __init__(self, entity_name: str, entity_id: str):
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} с ID {entity_id} не найдена")


class DuplicateEntityException(DomainException):
    """Дублирование сущности."""
    
    def __init__(self, entity_name: str, field: str, value: str):
        self.entity_name = entity_name
        self.field = field
        self.value = value
        super().__init__(
            f"{entity_name} с {field}='{value}' уже существует"
        )
