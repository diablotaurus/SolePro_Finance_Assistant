"""
Общие утилиты для приложения.
"""


class Singleton(type):
    """
    Метакласс для реализации паттерна Singleton.

    Пример использования:
        class MyClass(metaclass=Singleton):
            pass
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
