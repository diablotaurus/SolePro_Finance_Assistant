"""
Доменная сущность контрагента.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from ..constants import MAX_COUNTERPARTY_NAME_LENGTH
from ..exceptions.domain_exceptions import InvalidCounterpartyException


@dataclass(frozen=True)
class Counterparty:
    """
    Сущность контрагента.

    Атрибуты:
        id: Уникальный идентификатор контрагента
        name: Наименование контрагента
        description: Описание (необязательно)
        contact_info: Контактная информация
        created_at: Время создания
        updated_at: Время последнего обновления
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: Optional[str] = None
    contact_info: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Проверить инварианты домена после инициализации."""
        self._validate()

    def _validate(self) -> None:
        """Проверить бизнес-правила контрагента."""
        errors = []

        # Наименование обязательно.
        if not self.name or not self.name.strip():
            errors.append("Наименование контрагента обязательно")

        # Имя не должно быть слишком длинным.
        if len(self.name) > MAX_COUNTERPARTY_NAME_LENGTH:
            errors.append(
                f"Наименование контрагента не должно превышать "
                f"{MAX_COUNTERPARTY_NAME_LENGTH} символов"
            )

        # Управляющие символы в имени запрещены.
        if any(char in self.name for char in ['\x00', '\n', '\r', '\t']):
            errors.append("Наименование содержит недопустимые символы")

        if errors:
            raise InvalidCounterpartyException(
                f"Ошибка валидации контрагента: {'; '.join(errors)}"
            )

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        contact_info: Optional[str] = None,
    ) -> "Counterparty":
        """
        Создать новую версию контрагента с обновленными значениями.

        Возвращает новый объект Counterparty, так как сущность immutable.
        """
        from dataclasses import replace

        return replace(
            self,
            name=name if name is not None else self.name,
            description=description if description is not None else self.description,
            contact_info=contact_info if contact_info is not None else self.contact_info,
            updated_at=datetime.now(),
        )

    @property
    def is_valid(self) -> bool:
        """Проверка валидности контрагента."""
        try:
            self._validate()
            return True
        except InvalidCounterpartyException:
            return False

    def __str__(self) -> str:
        return f"Контрагент: {self.name}"
