# Telegram Moderation Bot

Telegram-бот для автоматической модерации групповых чатов. Удаляет сообщения с нецензурной лексикой, отправляет предупреждение пользователю, ведёт файловые логи и сохраняет историю действий в удалённой PostgreSQL.

Стек: **Python 3.12**, **aiogram 3**, **asyncpg**, **Docker**.

---

## Содержание

- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Структура проекта](#структура-проекта)
- [Требования](#требования)
- [Быстрый старт](#быстрый-старт)
- [Настройка Telegram](#настройка-telegram)
- [Конфигурация (.env)](#конфигурация-env)
- [Запуск](#запуск)
- [Логирование](#логирование)
- [База данных](#база-данных)
- [Фильтр нецензурной лексики](#фильтр-нецензурной-лексики)
- [Устранение неполадок](#устранение-неполадок)
- [Разработка и расширение](#разработка-и-расширение)
- [Деплой на VPS](#деплой-на-vps)
- [CI/CD (GitHub Actions)](#cicd-github-actions)
- [Безопасность](#безопасность)

---

## Возможности

- Модерация сообщений в **группах** и **супергруппах**
- Удаление сообщений с матом (текст и подписи к медиа)
- Предупреждение пользователю после удаления (с автоудалением через N секунд)
- Логирование через стандартный модуль `logging` в файл `logs/bot.log`
- Запись всех действий в PostgreSQL (удалённая БД)
- Запуск через Docker Compose или локально
- Скрипты `start.bat` / `stop.bat` для Windows

---

## Архитектура

```
Telegram API
     │
     ▼
┌─────────────┐     ┌──────────────────┐
│  aiogram    │────▶│ handlers/        │  обработка сообщений
│  (polling)  │     │ moderation.py    │
└─────────────┘     └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
      filters/profanity  utils/warnings  utils/database
              │              │              │
              ▼              ▼              ▼
         regex + словарь   предупреждение  PostgreSQL
                             в чат
```

**Поток обработки сообщения:**

1. Бот получает сообщение в группе.
2. Запись в лог и БД (`incoming_message`).
3. Проверка текста/caption фильтром `contains_profanity()`.
4. Если мат найден — удаление сообщения.
5. Запись в БД (`message_deleted`) + предупреждение в чат (`warning_sent`).
6. Предупреждение автоматически удаляется через `WARNING_TTL_SECONDS`.

---

## Структура проекта

```
MCP_CASE/
├── bot/
│   └── main.py              # Точка входа, polling, lifecycle
├── config/
│   └── settings.py          # Настройки из .env (pydantic-settings)
├── handlers/
│   └── moderation.py        # Обработчик групповых сообщений
├── filters/
│   └── profanity.py         # Словарь и regex-фильтр мата
├── logging_config/
│   └── setup.py             # Настройка logging → файл + консоль
├── utils/
│   ├── database.py          # asyncpg, пул соединений, история действий
│   └── warnings.py          # Отправка предупреждений в чат
├── logs/                    # Файлы логов (в .gitignore)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── start.bat                # Запуск на Windows
├── stop.bat                 # Остановка на Windows
├── .env.example             # Шаблон конфигурации
└── .env                     # Ваши секреты (не коммитить!)
```

---

## Требования

| Компонент | Версия |
|-----------|--------|
| Python | 3.12+ (для локального запуска) |
| Docker Desktop | актуальная (для Docker-запуска) |
| PostgreSQL | удалённый сервер (например AlwaysData) |
| Telegram Bot Token | от [@BotFather](https://t.me/BotFather) |

---

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone https://github.com/alex0572/Moderator_bot.git
cd Moderator_bot
```

### 2. Создать `.env`

```bash
copy .env.example .env
```

Заполните токен бота и параметры PostgreSQL (см. [Конфигурация](#конфигурация-env)).

### 3. Настроить бота в Telegram

См. раздел [Настройка Telegram](#настройка-telegram).

### 4. Запустить

**Windows (двойной клик или терминал):**

```cmd
start.bat
```

**Docker Compose:**

```bash
docker compose up -d --build
```

### 5. Проверить

```bash
docker compose ps
docker compose logs -f
```

Отправьте в группу тестовое сообщение со словом из фильтра — сообщение должно удалиться, появится предупреждение.

---

## Настройка Telegram

### Создание бота

1. Откройте [@BotFather](https://t.me/BotFather).
2. Команда `/newbot` → следуйте инструкциям.
3. Скопируйте токен в `.env` → `TELEGRAM_BOT_TOKEN`.

### Обязательные настройки для модерации

| Настройка | Где | Зачем |
|-----------|-----|-------|
| **Group Privacy → Turn off** | BotFather → Bot Settings | Бот видит все сообщения в группе |
| **Права администратора** | Настройки группы → Администраторы | Право **удалять сообщения** |
| **Добавить в группу** | Группа → Участники | Бот должен быть участником чата |

> Без отключения Privacy Mode бот получает только команды, ответы на свои сообщения и упоминания — обычные сообщения для модерации не приходят.

---

## Конфигурация (.env)

Скопируйте `.env.example` в `.env` и заполните:

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here

# PostgreSQL (удалённая БД)
DB_HOST=postgresql.example.net
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
DB_SCHEMA=public

# Логирование
LOG_DIR=logs
LOG_FILE=bot.log
LOG_LEVEL=INFO

# Предупреждения в чате
WARNING_ENABLED=true
WARNING_TTL_SECONDS=15
WARNING_MESSAGE=⚠️ {user}, ваше сообщение удалено: запрещена нецензурная лексика.
```

### Переменные окружения

| Переменная | Обязательная | По умолчанию | Описание |
|------------|:------------:|--------------|----------|
| `TELEGRAM_BOT_TOKEN` | да | — | Токен бота от BotFather |
| `DB_HOST` | да | — | Хост PostgreSQL |
| `DB_PORT` | нет | `5432` | Порт PostgreSQL |
| `DB_NAME` | да | — | Имя базы данных |
| `DB_USER` | да | — | Пользователь БД |
| `DB_PASSWORD` | да | — | Пароль БД |
| `DB_SCHEMA` | нет | `public` | Схема (зарезервировано) |
| `LOG_DIR` | нет | `logs` | Папка для логов |
| `LOG_FILE` | нет | `bot.log` | Имя файла лога |
| `LOG_LEVEL` | нет | `INFO` | Уровень: DEBUG, INFO, WARNING, ERROR |
| `WARNING_ENABLED` | нет | `true` | Отправлять предупреждение после удаления |
| `WARNING_TTL_SECONDS` | нет | `15` | Через сколько секунд удалить предупреждение (0 = не удалять) |
| `WARNING_MESSAGE` | нет | см. пример | Текст предупреждения; `{user}` — упоминание автора |

После изменения `.env` перезапустите контейнер:

```bash
docker compose up -d --build
```

---

## Запуск

### Docker Compose (рекомендуется)

```bash
# Запуск в фоне
docker compose up -d --build

# Просмотр логов
docker compose logs -f

# Остановка
docker compose down

# Статус
docker compose ps
```

Контейнер: `telegram-moderation-bot`  
Политика перезапуска: `unless-stopped` (автоперезапуск при падении Docker).

### Windows — скрипты

| Файл | Действие |
|------|----------|
| `start.bat` | Проверяет Docker и `.env`, выполняет `docker compose up -d --build` |
| `stop.bat` | Выполняет `docker compose down` |

**Автозапуск при входе в Windows:**

1. `Win + R` → `shell:startup` → Enter.
2. Создайте ярлык на `start.bat`.
3. В Docker Desktop включите *Start Docker Desktop when you log in*.

### Локальный запуск (без Docker)

```bash
pip install -r requirements.txt
python -m bot.main
```

Требуется доступ к PostgreSQL с вашей машины и файл `.env` в корне проекта.

---

## Логирование

Логи пишутся модулем `logging` в:

- **Файл:** `logs/bot.log` (ротация: 5 МБ × 5 файлов)
- **Консоль:** stdout (видно в `docker compose logs`)

Формат записи:

```
2026-05-21 12:00:00 | INFO     | moderation_bot.handlers | Incoming message: chat_id=... user_id=...
2026-05-21 12:00:01 | WARNING  | moderation_bot.handlers | Message deleted: chat_id=... user_id=...
2026-05-21 12:00:01 | WARNING  | moderation_bot.warnings   | Warning sent: chat_id=... user_id=...
2026-05-21 12:00:01 | ERROR    | moderation_bot.handlers | Delete failed ...
```

### Что логируется

| Событие | Уровень | Описание |
|---------|---------|----------|
| Входящее сообщение | INFO | chat_id, user_id, message_id |
| Удаление сообщения | WARNING | chat_id, user_id, message_id |
| Отправка предупреждения | WARNING | chat_id, user_id, warning_id |
| Ошибка удаления / БД | ERROR | Текст ошибки |

---

## База данных

При старте бот автоматически создаёт таблицу `moderation_actions` (если её нет).

### Схема таблицы

```sql
CREATE TABLE moderation_actions (
    id          SERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL,
    chat_id     BIGINT,
    action      TEXT NOT NULL,
    action_type VARCHAR(64) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Типы действий (`action_type`)

| Значение | Описание |
|----------|----------|
| `incoming_message` | Получено сообщение в группе |
| `message_deleted` | Сообщение удалено за мат |
| `warning_sent` | Отправлено предупреждение в чат |
| `error` | Ошибка (нет прав, сбой API, БД и т.д.) |

### Примеры SQL-запросов

```sql
-- Последние 20 действий
SELECT * FROM moderation_actions
ORDER BY created_at DESC
LIMIT 20;

-- Удалённые сообщения за сегодня
SELECT user_id, chat_id, action, created_at
FROM moderation_actions
WHERE action_type = 'message_deleted'
  AND created_at >= CURRENT_DATE;

-- Статистика по пользователю
SELECT action_type, COUNT(*)
FROM moderation_actions
WHERE user_id = 123456789
GROUP BY action_type;
```

---

## Фильтр нецензурной лексики

Файл: `filters/profanity.py`

- Базовый словарь русских и английских слов (`PROFANITY_WORDS`)
- Regex с границами слов (кириллица + латиница)
- Дополнительная проверка по токенам

### Расширение словаря

Добавьте слова в множество `PROFANITY_WORDS`:

```python
PROFANITY_WORDS: frozenset[str] = frozenset(
    {
        "бля",
        "новое_слово",
        # ...
    }
)
```

После изменений пересоберите Docker-образ:

```bash
docker compose up -d --build
```

### Проверяемые поля сообщения

- `message.text` — текст сообщения
- `message.caption` — подпись к фото/видео/документу

Сообщения без текста и подписи не проверяются.

---

## Устранение неполадок

| Проблема | Возможная причина | Решение |
|----------|-------------------|---------|
| Бот не реагирует на сообщения | Privacy Mode включён | BotFather → Group Privacy → **Turn off** |
| Сообщения не удаляются | Нет прав администратора | Выдайте право «Удалять сообщения» |
| Ошибка `Delete failed` в логах | Бот не админ или сообщение слишком старое | Проверьте права; Telegram не даёт удалять очень старые сообщения |
| Нет записей в БД | Неверный `.env` или нет доступа к серверу | Проверьте `DB_*`, firewall, доступ с хоста/Docker |
| `Docker не запущен` в start.bat | Docker Desktop выключен | Запустите Docker Desktop |
| Контейнер падает при старте | Неверный токен или БД | `docker compose logs` — смотрите traceback |
| Предупреждения не появляются | `WARNING_ENABLED=false` | Установите `true` в `.env` |
| После смены `.env` ничего не меняется | Старый контейнер | `docker compose up -d --build` |

### Полезные команды диагностики

```bash
# Логи контейнера
docker compose logs -f --tail 50

# Файл логов на хосте (Windows)
type logs\bot.log

# Проверка образа
docker images mcp_case-moderation-bot

# Пересоздание контейнера с нуля
docker compose down
docker compose up -d --build
```

---

## Разработка и расширение

### Зависимости

```
aiogram>=3.13.0,<4
asyncpg>=0.29.0,<1
pydantic-settings>=2.5.0,<3
python-dotenv>=1.0.0,<2
```

### Идеи для доработки

- Whitelist чатов (модерировать только выбранные группы)
- Команды для админов (`/stats`, `/ban`, `/mute`)
- Загрузка словаря из файла или БД
- Эскалация: предупреждение → mute → ban
- Webhook вместо polling (для production за reverse proxy)
- Уведомления администраторам в личку

### Добавление нового handler

1. Создайте файл в `handlers/`.
2. Определите `Router` и зарегистрируйте обработчики.
3. Подключите роутер в `bot/main.py`:

```python
dispatcher.include_router(your_router)
```

---

## Деплой на VPS

Бот использует **long polling** — достаточно VPS с Docker, публичный IP и открытые порты **не обязательны** (в отличие от webhook). PostgreSQL может оставаться на удалённом хосте (AlwaysData и т.п.).

### Минимальные требования к серверу

| Параметр | Рекомендация |
|----------|--------------|
| ОС | Ubuntu 22.04 / 24.04 LTS, Debian 12 |
| RAM | 512 MB – 1 GB |
| CPU | 1 vCPU |
| Диск | 5–10 GB |
| Сеть | исходящий доступ к `api.telegram.org` и вашему PostgreSQL |

### 1. Подготовка сервера

Подключитесь по SSH:

```bash
ssh user@your-server-ip
```

Обновите систему и установите Docker:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl

# Docker (официальный скрипт)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Выйдите и зайдите снова, чтобы группа `docker` применилась.

Проверка:

```bash
docker --version
docker compose version
```

### 2. Клонирование и настройка

```bash
cd ~
git clone https://github.com/alex0572/Moderator_bot.git
cd Moderator_bot
cp .env.example .env
nano .env   # заполните TELEGRAM_BOT_TOKEN и DB_*
```

Убедитесь, что VPS может достучаться до PostgreSQL (firewall хостинга БД, whitelist IP).

### 3. Первый запуск

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f --tail 30
```

Логи на диске сервера: `./logs/bot.log`.

### 4. Автозапуск после перезагрузки VPS

В `docker-compose.yml` уже указано `restart: unless-stopped` — контейнер поднимется после рестарта Docker.

Дополнительно включите автозапуск Docker:

```bash
sudo systemctl enable docker
```

### 5. Обновление версии на сервере

```bash
cd ~/Moderator_bot
git pull origin main
docker compose up -d --build
docker compose logs -f --tail 20
```

### 6. (Опционально) systemd unit

Если нужен явный сервис вместо ручного `docker compose`:

```bash
sudo nano /etc/systemd/system/moderation-bot.service
```

```ini
[Unit]
Description=Telegram Moderation Bot
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/user/Moderator_bot
ExecStart=/usr/bin/docker compose up -d --build
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable moderation-bot
sudo systemctl start moderation-bot
sudo systemctl status moderation-bot
```

Замените `/home/user/Moderator_bot` на реальный путь.

### 7. Мониторинг на VPS

```bash
# Статус контейнера
docker compose ps

# Логи в реальном времени
docker compose logs -f

# Использование ресурсов
docker stats telegram-moderation-bot

# Проверка записей в БД (на сервере БД)
# SELECT COUNT(*) FROM moderation_actions WHERE created_at > NOW() - INTERVAL '1 hour';
```

### Webhook vs polling на VPS

| Режим | Когда использовать |
|-------|-------------------|
| **Polling** (текущий) | Простой деплой, не нужен HTTPS и домен |
| **Webhook** | Высокая нагрузка, несколько инстансов; нужны домен, SSL, reverse proxy (nginx/Caddy) |

Для большинства сценариев модерации polling на VPS достаточно.

---

## CI/CD (GitHub Actions)

Пример pipeline: при push в `main` — проверка синтаксиса Python и автоматический деплой на VPS по SSH.

### Общая схема

```
git push → GitHub Actions
              ├── job: test (compileall)
              └── job: deploy (SSH → git pull → docker compose up)
```

### 1. Секреты репозитория

GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret | Описание |
|--------|----------|
| `VPS_HOST` | IP или домен сервера |
| `VPS_USER` | SSH-пользователь (например `ubuntu`) |
| `VPS_SSH_KEY` | Приватный SSH-ключ (содержимое `id_rsa`) |
| `VPS_PORT` | (опционально) порт SSH, по умолчанию 22 |

`.env` **не** храните в GitHub — он должен уже лежать на VPS в папке проекта.

### 2. SSH-ключ для деплоя

На локальной машине:

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f deploy_key -N ""
```

- Публичный ключ `deploy_key.pub` → на VPS в `~/.ssh/authorized_keys`
- Приватный ключ `deploy_key` → в секрет `VPS_SSH_KEY`

### 3. Пример workflow

Создайте файл `.github/workflows/deploy.yml` в репозитории:

```yaml
name: CI/CD

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Syntax check
        run: python -m compileall config bot handlers filters logging_config utils

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'
    steps:
      - name: Deploy to VPS
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          port: ${{ secrets.VPS_PORT || 22 }}
          script: |
            set -e
            cd ~/Moderator_bot
            git pull origin main || git pull origin master
            docker compose up -d --build
            docker compose ps
            docker image prune -f
```

> Путь `~/Moderator_bot` и ветка должны совпадать с вашим сервером.

### 4. Что делает pipeline

**Job `test`** (на каждый push и PR):

- checkout кода;
- установка зависимостей;
- `compileall` — проверка синтаксиса всех модулей.

**Job `deploy`** (только push в `main`/`master` после успешного test):

- SSH на VPS;
- `git pull`;
- `docker compose up -d --build`;
- очистка старых образов.

### 5. Ручной деплой (альтернатива CI)

Если CI пока не нужен:

```bash
ssh user@your-server-ip "cd ~/Moderator_bot && git pull && docker compose up -d --build"
```

### 6. Рекомендации для production CI/CD

- **Отдельная ветка** `develop` для разработки, деплой только из `main`.
- **Уведомления** — добавить шаг Telegram/Slack при падении deploy (через `if: failure()`).
- **Rollback** — на VPS: `git checkout <commit>` + `docker compose up -d --build`.
- **Не деплоить `.env`** — один раз создать вручную на сервере; в Actions передавать только секреты инфраструктуры (SSH).
- **Healthcheck** — после deploy проверять `docker compose logs --tail 5` на строку `Bot started, polling updates`.

### 7. Проверка после автодеплоя

```bash
# На VPS
docker compose ps
docker compose logs --tail 20

# В Telegram — тестовое сообщение в группе
# В БД — новая запись incoming_message
```

---

## Безопасность

- **Не коммитьте `.env`** — файл в `.gitignore`; в репозитории только `.env.example`.
- **Токен бота** — при утечке перевыпустите в BotFather (`/revoke`).
- **Пароль БД** — смените, если попал в публичный репозиторий.
- **Права бота** — выдавайте минимум необходимого (удаление сообщений, без лишних прав).

---

## Лицензия

Проект создан в учебных/личных целях. Используйте и дорабатывайте по своему усмотрению.
