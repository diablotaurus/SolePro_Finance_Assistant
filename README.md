# SolePro Finance Assistant 🚀

Современная система учета финансов для индивидуальных предпринимателей, построенная на принципах Clean Architecture.

## 🌟 Особенности

- **Clean Architecture** - четкое разделение ответственности между слоями
- **Dependency Injection** - управление зависимостями через контейнер
- **SQLAlchemy + PostgreSQL** - промышленная база данных с миграциями
- **PyQt6 Desktop App** - полнофункциональное десктопное приложение
- **Telegram Bot** - удобный бот для быстрого учета
- **Docker Support** - готовность к контейнеризации
- **Полностью типизированный** - type hints везде
- **Тестируемый код** - модульные и интеграционные тесты

## 🏗️ Архитектура

SolePro_Finance_Assistant/
├── src/solepro/
│ ├── core/ # ЯДРО (не зависит ни от чего)
│ │ ├── domain/ # Сущности и бизнес-правила
│ │ ├── application/ # Use Cases и DTO
│ │ └── ports/ # Интерфейсы (абстракции)
│ │
│ ├── infrastructure/ # ИНФРАСТРУКТУРА
│ │ ├── database/ # SQLAlchemy модели и репозитории
│ │ ├── config/ # Конфигурация приложения
│ │ └── di/ # Dependency Injection
│ │
│ ├── presentation/ # ПРЕДСТАВЛЕНИЕ
│ │ ├── desktop/ # PyQt6 приложение
│ │ └── telegram/ # Telegram бот
│ │
│ └── shared/ # ОБЩИЕ УТИЛИТЫ
│ ├── utils/ # Утилиты
│ ├── validators/ # Валидаторы данных
│ ├── formatters/ # Форматтеры
│ └── exceptions/ # Исключения
│
├── alembic/ # МИГРАЦИИ БАЗЫ ДАННЫХ
├── docker/ # КОНТЕЙНЕРИЗАЦИЯ
├── docs/ # ДОКУМЕНТАЦИЯ
├── scripts/ # СКРИПТЫ
└── tests/ # ТЕСТЫ


## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Клонировать репозиторий
git clone <repository-url>
cd SolePro_Finance_Assistant

# Установить зависимости
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Для разработки

2. Настройка окружения

# Скопировать шаблон .env файла
cp .env.example .env

# Отредактировать .env файл (указать токен бота, настройки БД и т.д.)

3. Инициализация базы данных

# Создать таблицы в базе данных
python scripts/init_db.py

# Или через Alembic миграции
alembic upgrade head

4. Запуск приложений

# Десктопное приложение
python -m solepro.presentation.desktop.application

# Telegram бот
python -m solepro.presentation.telegram.bot

# Или через скрипты
python RunDesktopApp.pyw
python RunBot.bat

🐳 Docker

# Запустить PostgreSQL и PgAdmin
docker-compose up -d postgres pgadmin

# Собрать и запустить приложение
docker-compose up --build app

🧪 Тестирование

# Запустить все тесты
pytest

# Запустить тесты с покрытием
pytest --cov=src/solepro --cov-report=html

# Запустить определенные тесты
pytest src/tests/test_domain.py -v

🔧 Разработка
Code Style

# Форматирование кода
black src/
isort src/

# Проверка типов
mypy src/

# Проверка стиля
flake8 src/

Миграции базы данных

# Создать новую миграцию
alembic revision --autogenerate -m "Описание изменений"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1

📚 Документация
Архитектура - описание архитектуры проекта

API - документация API (если будет REST API)

Развертывание - руководство по развертыванию

🛠️ Технологический стек
Python 3.9+ - основной язык

SQLAlchemy 2.0 - ORM для работы с БД

Alembic - миграции базы данных

PostgreSQL - основная база данных (SQLite для разработки)

PyQt6 - десктопное приложение

python-telegram-bot - Telegram бот

Pydantic - валидация данных

Dependency Injector - dependency injection

Docker - контейнеризация

Pytest - тестирование

🤝 Вклад в проект
Форкните репозиторий

Создайте ветку для вашей функции (git checkout -b feature/amazing-feature)

Зафиксируйте изменения (git commit -m 'Add amazing feature')

Запушьте ветку (git push origin feature/amazing-feature)

Откройте Pull Request

📄 Лицензия
Этот проект распространяется под лицензией MIT. Подробнее см. в файле LICENSE.

👨‍💻 Автор
Diablotaurus - GitHub

🙏 Благодарности
Сообществу Python за потрясающие инструменты

Разработчикам PyQt6 за отличный фреймворк

Всем контрибьюторам проекта

⭐ Если этот проект был полезен, поставьте звезду на GitHub!




---

Этот пакет завершает **полную новую архитектуру проекта**. Теперь у вас есть:

## ✅ ЧТО БЫЛО СОЗДАНО:

1. **Core слой** - доменные сущности, value objects, use cases
2. **Infrastructure слой** - SQLAlchemy модели, репозитории, DI контейнер
3. **Presentation слой** - Desktop приложение (PyQt6) и Telegram бот
4. **Shared утилиты** - валидаторы, форматтеры, исключения
5. **Тесты** - unit и integration тесты
6. **Миграции** - Alembic миграции для базы данных
7. **Скрипты** - инициализация БД и миграция данных
8. **Docker** - полная конфигурация для контейнеризации
9. **Документация** - README и структура документации

## 🚀 КАК ЗАПУСТИТЬ НОВУЮ АРХИТЕКТУРУ:

1. **Настройте окружение:**
   ```bash
   cp .env.example .env
   # Отредактируйте .env файл
   
2. Установите зависимости:

bash
pip install -r requirements.txt
pip install -r requirements-dev.txt

3. Инициализируйте БД:

bash
python scripts/init_db.py

4. Запустите приложения:

bash
# Desktop приложение
python -m solepro.presentation.desktop.application

# Или Telegram бот
python -m solepro.presentation.telegram.bot