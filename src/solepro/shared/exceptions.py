"""
Общие исключения приложения.
"""
from typing import Any


class AppException(Exception):
    """Базовое исключение приложения."""
    
    def __init__(self, message: str = "Произошла ошибка в приложении"):
        self.message = message
        super().__init__(self.message)
    
    def __str__(self) -> str:
        return self.message


class ValidationException(AppException):
    """Исключение валидации данных."""
    
    def __init__(self, message: str = "Ошибка валидации данных", field: str = None, value: Any = None):
        self.field = field
        self.value = value
        super().__init__(message)


class ConfigurationException(AppException):
    """Исключение конфигурации."""
    
    def __init__(self, message: str = "Ошибка конфигурации приложения"):
        super().__init__(message)


class DatabaseException(AppException):
    """Исключение базы данных."""
    
    def __init__(self, message: str = "Ошибка базы данных", sql: str = None, params: tuple = None):
        self.sql = sql
        self.params = params
        super().__init__(message)


class NotFoundException(AppException):
    """Исключение - объект не найден."""
    
    def __init__(self, entity: str = "Объект", entity_id: Any = None):
        self.entity = entity
        self.entity_id = entity_id
        message = f"{entity} не найден"
        if entity_id is not None:
            message += f" (ID: {entity_id})"
        super().__init__(message)


class AlreadyExistsException(AppException):
    """Исключение - объект уже существует."""
    
    def __init__(self, entity: str = "Объект", field: str = None, value: Any = None):
        self.entity = entity
        self.field = field
        self.value = value
        message = f"{entity} уже существует"
        if field and value is not None:
            message += f" ({field}: {value})"
        super().__init__(message)


class PermissionDeniedException(AppException):
    """Исключение - доступ запрещен."""
    
    def __init__(self, message: str = "Доступ запрещен", required_permission: str = None):
        self.required_permission = required_permission
        super().__init__(message)


class AuthenticationException(AppException):
    """Исключение аутентификации."""
    
    def __init__(self, message: str = "Ошибка аутентификации"):
        super().__init__(message)


class AuthorizationException(AppException):
    """Исключение авторизации."""
    
    def __init__(self, message: str = "Ошибка авторизации"):
        super().__init__(message)


class BusinessRuleException(AppException):
    """Исключение нарушения бизнес-правила."""
    
    def __init__(self, message: str = "Нарушение бизнес-правила"):
        super().__init__(message)


class ExternalServiceException(AppException):
    """Исключение внешнего сервиса."""
    
    def __init__(self, service: str = "Внешний сервис", message: str = "Ошибка внешнего сервиса"):
        self.service = service
        full_message = f"Ошибка {service}: {message}"
        super().__init__(full_message)


class NetworkException(AppException):
    """Исключение сети."""
    
    def __init__(self, message: str = "Сетевая ошибка", url: str = None, status_code: int = None):
        self.url = url
        self.status_code = status_code
        super().__init__(message)


class TimeoutException(AppException):
    """Исключение таймаута."""
    
    def __init__(self, message: str = "Таймаут операции", timeout: float = None):
        self.timeout = timeout
        if timeout is not None:
            message = f"Таймаут операции ({timeout} секунд)"
        super().__init__(message)


class RateLimitException(AppException):
    """Исключение ограничения частоты запросов."""
    
    def __init__(self, message: str = "Превышен лимит запросов", retry_after: int = None):
        self.retry_after = retry_after
        if retry_after is not None:
            message = f"Превышен лимит запросов. Повторите через {retry_after} секунд"
        super().__init__(message)


class SerializationException(AppException):
    """Исключение сериализации."""
    
    def __init__(self, message: str = "Ошибка сериализации данных", data_type: str = None):
        self.data_type = data_type
        super().__init__(message)


class DeserializationException(AppException):
    """Исключение десериализации."""
    
    def __init__(self, message: str = "Ошибка десериализации данных", data_type: str = None):
        self.data_type = data_type
        super().__init__(message)


class FileSystemException(AppException):
    """Исключение файловой системы."""
    
    def __init__(self, message: str = "Ошибка файловой системы", path: str = None, operation: str = None):
        self.path = path
        self.operation = operation
        super().__init__(message)


class ImportException(AppException):
    """Исключение импорта."""
    
    def __init__(self, message: str = "Ошибка импорта данных", source: str = None):
        self.source = source
        super().__init__(message)


class ExportException(AppException):
    """Исключение экспорта."""
    
    def __init__(self, message: str = "Ошибка экспорта данных", format: str = None, destination: str = None):
        self.format = format
        self.destination = destination
        super().__init__(message)


class NotificationException(AppException):
    """Исключение уведомлений."""
    
    def __init__(self, message: str = "Ошибка отправки уведомления", channel: str = None):
        self.channel = channel
        super().__init__(message)


class CacheException(AppException):
    """Исключение кэша."""
    
    def __init__(self, message: str = "Ошибка кэша", key: str = None, operation: str = None):
        self.key = key
        self.operation = operation
        super().__init__(message)


class DependencyException(AppException):
    """Исключение зависимостей."""
    
    def __init__(self, message: str = "Ошибка зависимостей", dependency: str = None):
        self.dependency = dependency
        super().__init__(message)


class MigrationException(AppException):
    """Исключение миграции."""
    
    def __init__(self, message: str = "Ошибка миграции", version: str = None):
        self.version = version
        super().__init__(message)


class BackupException(AppException):
    """Исключение резервного копирования."""
    
    def __init__(self, message: str = "Ошибка резервного копирования", backup_type: str = None):
        self.backup_type = backup_type
        super().__init__(message)


class ResourceExhaustedException(AppException):
    """Исключение исчерпания ресурсов."""
    
    def __init__(self, message: str = "Ресурсы исчерпаны", resource: str = None, limit: Any = None):
        self.resource = resource
        self.limit = limit
        super().__init__(message)


class MaintenanceException(AppException):
    """Исключение технического обслуживания."""
    
    def __init__(self, message: str = "Техническое обслуживание", estimated_duration: str = None):
        self.estimated_duration = estimated_duration
        super().__init__(message)
