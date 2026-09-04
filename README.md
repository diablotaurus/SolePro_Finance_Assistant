# SolePro Finance Assistant 🚀

[![Tests](https://github.com/diablotaurus/SolePro_Finance_Assistant/actions/workflows/tests.yml/badge.svg)](https://github.com/diablotaurus/SolePro_Finance_Assistant/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Система учёта доходов и расходов от предпринимательской деятельности для индивидуальных предпринимателей (ИП). Включает **десктопное приложение** (PyQt6) и **Telegram-бота**, построена на принципах **Clean Architecture**, **OOP**, **DRY** и **SOLID**.

---

## ✨ Возможности

- 🧾 Учёт транзакций: доход, расход, налог, прибыль, контрагент, примечание
- 👥 Справочник контрагентов с агрегатами по доходу
- 📊 Статистика: помесячная разбивка, сравнение периодов, топ контрагентов
- 🔎 Фильтрация и поиск (по датам, типу, налогу, сумме, тексту)
- 📤 Экспорт транзакций в Excel
- 🖥️ Десктопное приложение на PyQt6
- 🤖 Telegram-бот для быстрого учёта
- 🗄️ SQLite (по умолчанию) и PostgreSQL, миграции через Alembic
- 🧪 235 автотестов, CI на GitHub Actions

---

## 🛠️ Технологический стек

| Технология | Назначение |
|---|---|
| **Python 3.13** | Основной язык |
| **SQLAlchemy 2.0** | ORM |
| **Alembic** | Миграции БД |
| **SQLite / PostgreSQL** | Базы данных (dev / prod) |
| **Pydantic 2 / pydantic-settings** | Валидация DTO |
| **PyQt6** | Десктопное приложение |
| **python-telegram-bot** | Telegram-бот |
| **dependency-injector** | Внедрение зависимостей (DI) |
| **pandas / openpyxl** | Экспорт в Excel |
| **pytest / pytest-qt** | Тестирование |

---

## 🏗️ Архитектура

Проект следует **Clean Architecture**: зависимости направлены внутрь, доменный слой не зависит ни от чего внешнего.

```
src/solepro/
├── core/                       # ЯДРО (бизнес-логика)
│   ├── domain/                 # Сущности, value objects, перечисления,
│   │                           #   исключения, интерфейсы репозиториев
│   └── application/            # Use Cases, DTO, mappers,
│                               #   specifications, unit_of_work
│
├── infrastructure/             # ИНФРАСТРУКТУРА
│   ├── config/                 # Конфигурация из переменных окружения
│   ├── database/               # SQLAlchemy: модели, репозитории,
│   │                           #   session_manager, unit_of_work, миграции
│   └── di/                     # Контейнер зависимостей
│
├── presentation/               # ПРЕДСТАВЛЕНИЕ
│   ├── desktop/                # PyQt6 приложение
│   └── telegram/               # Telegram-бот
│
└── shared/                     # ОБЩИЕ УТИЛИТЫ
    ├── exceptions.py           # Исключения
    ├── formatters.py           # Форматтеры
    ├── utils.py                # Утилиты
    ├── validators.py           # Валидаторы
    └── logging_config.py       # Единая настройка логирования

alembic/        # Миграции базы данных
docker/         # Контейнеризация
docs/           # Документация и changelog
scripts/        # Установка, обновление, бэкап и служебные скрипты
src/tests/      # Тесты
```

---

## 📋 Требования

- **Windows 10/11** — основной поддерживаемый сценарий для desktop-приложения;
- **Python 3.13 или новее**;
- **Git** — для клонирования и обновления проекта;
- доступ в интернет для установки зависимостей;
- VPN или прокси может потребоваться для Telegram-бота, если `api.telegram.org`
  недоступен напрямую.

Для desktop-приложения PostgreSQL не обязателен: по умолчанию используется
локальная SQLite-база `data/finances.db`.

---

## 🚀 Быстрый старт

### Рекомендуемая установка на Windows

```powershell
git clone https://github.com/diablotaurus/SolePro_Finance_Assistant.git
cd SolePro_Finance_Assistant
setup.bat
```

Установщик автоматически:

1. найдёт Python 3.13+;
2. создаст `.venv`;
3. установит зависимости;
4. создаст `.env` из `.env.example`, если файла ещё нет;
5. подготовит рабочие каталоги;
6. применит миграции и инициализирует базу данных.

Существующий `.env` **никогда не перезаписывается**.

Дополнительные варианты:

```powershell
# Установить также зависимости разработчика
setup.bat -Dev

# Не инициализировать базу данных
setup.bat -SkipDatabase
```

### Ручная установка

#### 1. Клонировать репозиторий

```bash
git clone https://github.com/diablotaurus/SolePro_Finance_Assistant.git
cd SolePro_Finance_Assistant
```

#### 2. Создать виртуальное окружение

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate
```

#### 3. Установить зависимости

```bash
pip install -r requirements.txt
pip install --no-deps -e .
pip install -r requirements-dev.txt   # для разработки и тестов
```

#### 4. Настроить окружение

```bash
# Windows
copy .env.example .env
# Linux / macOS
cp .env.example .env
```

Откройте `.env` и заполните значения (минимум — `TELEGRAM_BOT_TOKEN`, если нужен бот). См. раздел **«Конфигурация (.env)»** ниже.

#### 5. Инициализировать базу данных

```bash
python scripts/init_db.py
# или через миграции Alembic
alembic upgrade head
```

#### 6. Запуск

См. раздел **«Запуск»** ниже.

---

## ⚙️ Конфигурация (.env)

Конфигурация читается из файла `.env` (шаблон — `.env.example`). Ключевые переменные:

| Переменная | Описание | Пример |
|---|---|---|
| `APP_ENV` | Окружение | `development` |
| `APP_SECRET_KEY` | Секретный ключ приложения | `change-me` |
| `DATABASE_URL` | Строка подключения к БД | `sqlite:///./data/finances.db` |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота (от @BotFather) | `123456:ABC...` |
| `TELEGRAM_ALLOWED_USERS` | Разрешённые user ID (через запятую) | `123456789,987654321` |
| `TELEGRAM_ADMIN_CHAT_ID` | ID администратора | `123456789` |
| `TELEGRAM_LOG_FILE` | Файл лога Telegram-бота | `logs/bot.log` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `LOG_FILE` | Файл лога (desktop) | `logs/app.log` |
| `CURRENCY` | Валюта | `RUB` |

Для PostgreSQL укажите, например:
```
DATABASE_URL=postgresql://user:password@localhost:5432/solepro_finance
```

> ⚠️ **Безопасность:** файл `.env` содержит секреты (токен бота, ключи) и **не должен попадать в git** — он уже добавлен в `.gitignore`. Публикуйте только `.env.example` без реальных значений.

---

## 🖥️ Запуск

### Десктопное приложение

```bash
python -m solepro.presentation.desktop.application
```
На Windows удобнее:
- **`RunDesktopApp.pyw`** — двойной клик, запуск без консоли;
- **`DebugDesktopApp.bat`** — запуск с консолью (для отладки).

### Telegram-бот

```bash
python -m solepro.presentation.telegram.bot
```
На Windows — двойной клик по **`RunBot.bat`**.

---

## 🧪 Тесты

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=src/solepro --cov-report=html

# Конкретный файл
pytest src/tests/test_domain.py -v
```

Тесты автоматически запускаются в **GitHub Actions** на каждый `push` в `main` и на каждый pull request (см. бейдж **Tests** вверху).

---

## 🧑‍💻 Разработка

### Качество кода

```bash
black src/        # форматирование
isort src/        # сортировка импортов
mypy src/         # проверка типов
flake8 src/       # стиль
```

### Миграции базы данных

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Описание изменений"

# Применить миграции
alembic upgrade head

# Откатить последнюю
alembic downgrade -1
```

---

## 🐳 Docker

```bash
# Запустить PostgreSQL (и сопутствующие сервисы)
docker-compose up -d postgres

# Собрать и запустить приложение
docker-compose up --build app
```

---

## 📄 Лицензия

Проект распространяется под лицензией **MIT** — подробнее в файле [LICENSE](LICENSE).

## 👤 Автор

**Diablotaurus** — [GitHub](https://github.com/diablotaurus)

---

⭐ Если проект оказался полезен — поставьте звезду на GitHub!
