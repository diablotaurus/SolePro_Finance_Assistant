"""
Value Object для работы с денежными суммами.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Union, Optional
import locale

from ..exceptions.domain_exceptions import InvalidMoneyException


@dataclass(frozen=True)
class Money:
    """
    Value Object для представления денежных сумм.
    
    Атрибуты:
        value: Денежная сумма в виде Decimal
        currency: Валюта (по умолчанию 'RUB')
    """
    value: Decimal = Decimal('0')
    currency: str = "RUB"
    
    # Константы для валют
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    
    # Поддерживаемые валюты
    SUPPORTED_CURRENCIES = {RUB, USD, EUR}
    
    # Символы валют
    CURRENCY_SYMBOLS = {
        RUB: "₽",
        USD: "$",
        EUR: "€"
    }
    
    def __post_init__(self):
        """Валидация после инициализации."""
        if not isinstance(self.value, Decimal):
            try:
                normalized = Decimal(str(self.value))
            except (InvalidOperation, ValueError, TypeError) as exc:
                raise InvalidMoneyException("Значение должно быть типа Decimal") from exc
            object.__setattr__(self, "value", normalized)
        self._validate()
    
    def _validate(self) -> None:
        """Валидация денежной суммы."""
        errors = []
        
        # Проверка валюты
        if self.currency not in self.SUPPORTED_CURRENCIES:
            errors.append(f"Неподдерживаемая валюта: {self.currency}")
        
        # Проверка значения (Decimal)
        if not isinstance(self.value, Decimal):
            errors.append("Значение должно быть типа Decimal")

        # Проверка на слишком большие суммы (условно)
        if abs(self.value) > Decimal('1000000000'):  # 1 миллиард
            errors.append("Сумма слишком большая")
        
        if errors:
            raise InvalidMoneyException(
                f"Ошибка валидации денежной суммы: {'; '.join(errors)}"
            )
    
    @classmethod
    def from_string(cls, amount: str, currency: str = "RUB") -> "Money":
        """
        Создать Money из строки.
        
        Args:
            amount: Строка с суммой (например "1000.50" или "1,000.50")
            currency: Валюта
            
        Returns:
            Экземпляр Money
        """
        try:
            cleaned = amount.strip()
            if "," in cleaned and "." in cleaned:
                cleaned = cleaned.replace(",", "")
            else:
                cleaned = cleaned.replace(",", ".")

            cleaned = ''.join(char for char in cleaned if char.isdigit() or char in '.-')
            
            if not cleaned:
                raise ValueError("Пустая строка")
            
            decimal_value = Decimal(cleaned)
            return cls(value=decimal_value, currency=currency)
        except (InvalidOperation, ValueError) as e:
            raise InvalidMoneyException(f"Неверный формат суммы: {amount}") from e
    
    @classmethod
    def from_float(cls, amount: float, currency: str = "RUB") -> "Money":
        """
        Создать Money из float.
        
        Внимание: Избегайте float для денег из-за проблем с точностью.
        Используйте только для совместимости со старым кодом.
        """
        decimal_value = Decimal(str(amount))  # Преобразуем через строку для точности
        return cls(value=decimal_value, currency=currency)
    
    def to_decimal(self) -> Decimal:
        """Получить значение как Decimal."""
        return self.value
    
    def to_float(self) -> float:
        """Получить значение как float (с потерей точности)."""
        return float(self.value)
    
    def round(self, decimals: int = 2) -> "Money":
        """Округлить сумму до указанного количества знаков."""
        rounded_value = self.value.quantize(
            Decimal('0.' + '0' * decimals),
            rounding=ROUND_HALF_UP
        )
        return Money(value=rounded_value, currency=self.currency)
    
    def format(self, show_currency: bool = True, locale_name: Optional[str] = None) -> str:
        """
        Форматировать сумму для отображения.
        
        Args:
            show_currency: Показывать ли символ валюты
            locale_name: Локаль для форматирования (например 'ru_RU')
            
        Returns:
            Отформатированная строка
        """
        try:
            if locale_name:
                old_locale = locale.getlocale(locale.LC_MONETARY)
                locale.setlocale(locale.LC_MONETARY, locale_name)
            
            # Округляем до 2 знаков
            rounded = self.round(decimals=2)
            
            # Форматируем с разделителями тысяч
            if locale_name:
                formatted = locale.currency(
                    rounded.to_float(),
                    symbol=False,
                    grouping=True
                )
            else:
                # Простое форматирование без локали
                formatted = f"{rounded.value:,.2f}".replace(',', ' ').replace('.', ',')
            
            if show_currency:
                symbol = self.CURRENCY_SYMBOLS.get(self.currency, self.currency)
                return f"{formatted} {symbol}"
            
            return formatted
            
        finally:
            if locale_name:
                locale.setlocale(locale.LC_MONETARY, old_locale)
    
    def __str__(self) -> str:
        return self.format(show_currency=True, locale_name='ru_RU')
    
    def __repr__(self) -> str:
        return f"Money(value={self.value}, currency='{self.currency}')"
    
    # Арифметические операции
    def __add__(self, other: Union["Money", Decimal, int, float]) -> "Money":
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise InvalidMoneyException("Нельзя складывать разные валюты")
            return Money(value=self.value + other.value, currency=self.currency)
        elif isinstance(other, (Decimal, int, float)):
            return Money(value=self.value + Decimal(str(other)), currency=self.currency)
        else:
            return NotImplemented
    
    def __sub__(self, other: Union["Money", Decimal, int, float]) -> "Money":
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise InvalidMoneyException("Нельзя вычитать разные валюты")
            return Money(value=self.value - other.value, currency=self.currency)
        elif isinstance(other, (Decimal, int, float)):
            return Money(value=self.value - Decimal(str(other)), currency=self.currency)
        else:
            return NotImplemented
    
    def __mul__(self, other: Union[Decimal, int, float]) -> "Money":
        if isinstance(other, (Decimal, int, float)):
            return Money(value=self.value * Decimal(str(other)), currency=self.currency)
        else:
            return NotImplemented
    
    def __truediv__(self, other: Union[Decimal, int, float]) -> "Money":
        if isinstance(other, (Decimal, int, float)):
            if other == 0:
                raise InvalidMoneyException("Деление на ноль")
            return Money(value=self.value / Decimal(str(other)), currency=self.currency)
        else:
            return NotImplemented
    
    def __neg__(self) -> "Money":
        return Money(value=-self.value, currency=self.currency)
    
    def __abs__(self) -> "Money":
        return Money(value=abs(self.value), currency=self.currency)
    
    # Операции сравнения
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.value == other.value and self.currency == other.currency
    
    def __lt__(self, other: "Money") -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise InvalidMoneyException("Нельзя сравнивать разные валюты")
        return self.value < other.value
    
    def __le__(self, other: "Money") -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise InvalidMoneyException("Нельзя сравнивать разные валюты")
        return self.value <= other.value
    
    def __gt__(self, other: "Money") -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise InvalidMoneyException("Нельзя сравнивать разные валюты")
        return self.value > other.value
    
    def __ge__(self, other: "Money") -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise InvalidMoneyException("Нельзя сравнивать разные валюты")
        return self.value >= other.value
    
