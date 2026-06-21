# Порядок — backend (P0 + P1 + P2)

Бэкенд для «Порядка» — тихого личного места навести порядок в делах и людях.

**P0 = «оживить фронт»:** заменить `localStorage` реальным сервером с авторизацией.
API говорит на **JSON-модели существующего фронта** (см. бриф §2–§4): `GET/PUT /state`
отдают/принимают весь bundle, а внутри он раскладывается по сущностям.

**P1 = «душа»:** вычисление остывания клиентов из лога касаний, тёплые касания
(`/suggestions/touches`), спокойный утренний дайджест (`/digest/morning`), ночная
джоба пересчёта и по-сущностный CRUD. Тон — забота, не тревога; без счётчиков-долгов.

> P2 (Telegram + Claude: захват → подтверждение → запись) — следующий слой поверх той же
> базы; ему нужны ключи/бот.

## Definition of Done (P0) — выполнено

- [x] Скаффолд репозитория (§10), PostgreSQL + Alembic, модель `documents` + `links` + `users`.
- [x] `POST /auth/login`, `GET /state`, `PUT /state`; bundle (де)сериализуется в/из сущностей.
- [x] Сидер демо-данных (из начального состояния фронта).
- [x] Тесты: round-trip `PUT → GET` и защита эндпоинтов авторизацией (10 тестов).
- [x] README: локальный запуск, миграции, деплой на Railway/Render.

## Стек

Python 3.12 · FastAPI (async) · PostgreSQL · SQLAlchemy 2.0 · Alembic · Pydantic v2 ·
JWT (PyJWT) · bcrypt. Менеджер пакетов — [`uv`](https://docs.astral.sh/uv/).

## Архитектура (ключевые решения)

- **Контракт = JSON-модель фронта.** `GET/PUT /state` — это мост вместо `localStorage`.
  Git/markdown-слой **отложен** (вариант A из брифа §2): источник правды — БД.
- **Одна таблица `documents` (JSONB) на все сущности** + промотированные колонки
  (`done`, `today`, `last_touch_at`, `occurred_at`, `amount`, `subject_ref`) для будущих
  запросов. `links` — отдельная таблица (граф «сцепок»). Новый тип сущности добавляется
  без миграции.
- **Wire-формат = существующие ключи фронта** (`inbox`, `events2`, `events`), полным
  супермножеством — true drop-in. Внутри БД имена нормализованы
  (`thought`, `event`, `activity`, …); отображение — в `app/services/bundle.py`.
- **Безопасный merge на `PUT`.** Автосейв фронта присылает **частичный** bundle (без
  `projects/clients/directions`). Поэтому отсутствующий в payload тип **не трогается**, а
  присутствующий (даже `[]`) — заменяется. Иначе автосейв затирал бы клиентов.
- **Лог истории/денег заложен сразу** (тип `history`: `touch|order|session|invoice|note`
  + сумма, master §8). Модель и промо-колонки есть; вычисления LTV/остывания — это P1.
- **Auth:** один пользователь, email+пароль → долгоживущий JWT.

## Структура репозитория

```
app/
  main.py            # FastAPI app, CORS, роуты
  config.py          # pydantic-settings (env)
  db.py              # async engine, session, Base
  models.py          # User, Document, LinkEdge
  schemas.py         # Pydantic: StateBundle, Task, Client, …
  auth.py            # bcrypt, JWT, зависимость current_user
  api/
    auth.py          # POST /auth/login, GET /auth/me
    state.py         # GET/PUT /state                       (P0)
    proactive.py     # /suggestions/touches, /digest/morning (P1)
    entities.py      # per-entity CRUD + /links              (P1)
    telegram.py      # /telegram/webhook                     (P2)
  services/
    bundle.py        # StateBundle <-> documents/links/settings
    cooling.py       # client cooling / warm touches         (P1)
    digest.py        # morning digest                        (P1)
    llm.py           # Claude intent routing                 (P2)
    transcribe.py    # Whisper voice transcription           (P2)
    capture.py       # capture → confirm → write             (P2)
  jobs.py            # APScheduler nightly recompute          (P1)
  seed_data.py       # демо-данные (из фронта) + демо history-лог
  seed.py            # python -m app.seed
alembic/             # миграции (async env)
tests/               # 23 тестов (round-trip, auth, проактивность, CRUD, capture)
Dockerfile · render.yaml · railway.json · Procfile · .github/workflows/ci.yml
```

## Быстрый старт (локально, PostgreSQL)

```bash
# 0) зависимости
uv sync

# 1) база (один раз)
createdb poryadok   # или: psql -c "CREATE DATABASE poryadok;"
# создать роль, если нужно:
#   psql -c "CREATE ROLE poryadok LOGIN PASSWORD 'poryadok';"

# 2) конфиг
cp .env.example .env        # отредактировать DATABASE_URL / JWT_SECRET / AUTH_*

# 3) миграции + демо-данные
uv run alembic upgrade head
uv run python -m app.seed

# 4) запуск
uv run uvicorn app.main:app --reload
```

Открыть **http://localhost:8000/docs** (Swagger). Демо-логин: `demo@poryadok.app` / `poryadok`.

> Без `uv`: `python3.12 -m venv .venv && . .venv/bin/activate && pip install -e .`,
> затем те же команды без префикса `uv run`.

### Альтернатива без Postgres (быстрый прогон)

В `.env` укажите `DATABASE_URL=sqlite+aiosqlite:///./poryadok.db`, затем
`uv run alembic upgrade head && uv run python -m app.seed && uv run uvicorn app.main:app`.
Прод — всё равно Postgres.

## API

| Метод | Путь          | Описание                                   | Auth |
|-------|---------------|--------------------------------------------|------|
| POST  | `/auth/login` | `{email,password}` → `{access_token, token, token_type, expires_at}` | — |
| GET   | `/auth/me`    | текущий пользователь                        | ✓ |
| GET   | `/state`      | весь bundle (гидрация при загрузке)         | ✓ |
| PUT   | `/state`      | сохранить bundle (debounced-автосейв)       | ✓ |
| GET   | `/health`     | healthcheck                                 | — |
| GET   | `/suggestions/touches` | клиенты, которым пора тёплое касание (P1) | ✓ |
| GET   | `/digest/morning`      | спокойная сводка на день (P1)             | ✓ |
| —     | `/{tasks,thoughts,projects,clients,directions,events,quicklinks,services,history}` | CRUD по сущностям: `GET/POST` коллекция, `PATCH/DELETE /{id}` (P1) | ✓ |
| —     | `/links`      | граф «сцепок»: `GET/POST`, `DELETE /{id}` (P1) | ✓ |
| POST  | `/telegram/webhook` | захват из Telegram → подтверждение → запись (P2) | secret |

```bash
# логин → токен
TOKEN=$(curl -s -X POST localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@poryadok.app","password":"poryadok"}' | jq -r .access_token)

# прочитать состояние
curl -s localhost:8000/state -H "Authorization: Bearer $TOKEN" | jq 'keys'

# сохранить состояние (присылается как есть; отсутствующие типы не трогаются)
curl -s -X PUT localhost:8000/state -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d @bundle.json
```

### Контракт bundle

Ключи — как в `localStorage` фронта (`poryadok.data`, `ver: 2`):

`tasks` · `inbox` (мысли) · `directions` · `projects` · `clients` · `events2` (календарь) ·
`events` (лог активности) · `quickLinks` · `services` · `links` · `history` (лог денег, новое) ·
плюс пасстру `ver` / `seq` / `hapticOn` / `settings`.

Семантика `PUT`: ключ **присутствует** → коллекция этого типа заменяется (даже на `[]`);
ключ **отсутствует** → тип остаётся как был. `GET` всегда возвращает все ключи (пустые — `[]`).

## Тесты

```bash
uv run pytest          # 23 теста, на in-memory SQLite, без внешних сервисов
```

Покрывают: round-trip `PUT→GET`, безопасный merge частичного сейва, очистку типа
пустым списком, и что эндпоинты закрыты авторизацией.

## Деплой (Railway / Render)

Образ `Dockerfile` на старте сам прогоняет `alembic upgrade head` и поднимает Uvicorn.
Managed-Postgres отдаёт `postgres://…` — приложение само переписывает схему в asyncpg.

**Railway:** New Project → Deploy from repo (соберётся по `Dockerfile`, healthcheck из
`railway.json`) → добавить **PostgreSQL** (даст `DATABASE_URL`) → задать переменные →
один раз выполнить сид:
```bash
railway run python -m app.seed
```

**Render:** New → **Blueprint** (возьмёт `render.yaml`: web-сервис + Postgres) → задать
`AUTH_EMAIL` / `AUTH_PASSWORD` в дашборде (`JWT_SECRET` сгенерируется) → после первого
деплоя один раз `python -m app.seed` в Shell.

### Переменные окружения

| Переменная | Назначение | Дефолт |
|---|---|---|
| `DATABASE_URL` | строка подключения (`postgres://` тоже ок) | sqlite-файл |
| `AUTH_EMAIL` / `AUTH_PASSWORD` | единственный пользователь | `demo@poryadok.app` / `poryadok` |
| `JWT_SECRET` | подпись JWT (≥ 32 байт; `openssl rand -hex 32`) | dev-заглушка |
| `JWT_EXPIRE_DAYS` | срок жизни токена | `30` |
| `CORS_ORIGINS` | разрешённые origin фронта (через запятую) | `*` |
| `COOLING_WARM_DAYS` / `COOLING_COLD_DAYS` | пороги остывания | `7` / `21` |
| `SCHEDULER_ENABLED` | ночная джоба пересчёта остывания | `true` |
| `DIGEST_HOUR` | час (UTC) пересчёта | `7` |
| `TELEGRAM_BOT_TOKEN` | токен бота (наличие включает webhook) (P2) | — |
| `TELEGRAM_ALLOWED_USER_IDS` | whitelist id через запятую (P2) | — |
| `TELEGRAM_WEBHOOK_SECRET` | секрет для `setWebhook` (P2) | — |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | Claude-роутинг / Whisper (P2) | — |
| `ROUTER_MODEL` / `WHISPER_MODEL` | модели роутинга/транскрипции (P2) | `claude-sonnet-4-6` / `whisper-1` |

> Если managed-URL содержит `?sslmode=require`, уберите параметр (asyncpg использует свой
> SSL); для внутренних URL Railway/Render это обычно не нужно.

## Статус фаз

- **P0 ✅** — auth + `GET/PUT /state` (мост вместо localStorage), сидер, тесты, деплой.
- **P1 ✅** — остывание клиентов, `/suggestions/touches`, `/digest/morning`, ночная джоба,
  по-сущностный CRUD + `/links`.
- **P2 ✅ (код + юнит-тесты)** — Telegram + Claude: `/telegram/webhook`, транскрипция
  (Whisper), роутинг интента через Claude (forced tool), петля **захват → показать →
  подтверждение → запись** (таблица `pending_captures`), whitelist. Логика покрыта
  юнит-тестами с фейковым LLM; **живая интеграция требует ключей и бота** (см. ниже) —
  локально не прогонялась.
- **P3** — мультипользовательность, регистрация, биллинг, коннекторы.

### Telegram-бот (P2) — как поднять вживую

```bash
uv sync --extra ai            # ставит anthropic + openai (lazy-import в коде)
# в .env: TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USER_IDS, TELEGRAM_WEBHOOK_SECRET,
#         ANTHROPIC_API_KEY, OPENAI_API_KEY
# зарегистрировать webhook (после деплоя на публичный https):
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -d "url=https://<твой-домен>/telegram/webhook" \
  -d "secret_token=$TELEGRAM_WEBHOOK_SECRET"
```

Петля: сообщение (текст/голос) → (Whisper расшифровывает и показывает транскрипт) →
Claude классифицирует (задача/мысль/касание) → бот присылает черновик с кнопками
**Подтвердить / Отменить** → запись в БД только после подтверждения.

## Фронтенд

В `frontend/` — два пути (см. `frontend/README.md`):

- **`frontend/web/`** — реальный **React + Vite**-клиент «Главной», воссозданный по
  дизайн-исходнику `.dc` (тёплая «бумага», kodawari-light) и привязанный к API
  (`GET/PUT /state`, `/suggestions/touches`): чек-ин → фокус, задачи дня, быстрый
  захват, тёплое касание, недавнее, экран входа. Durable-путь. Запуск — `npm install &&
  npm run dev` в `frontend/web/`.
- **`frontend/bridge/`** — быстрый мост: патчер врезает логин + API вместо `localStorage`
  в экспортированный standalone-билд Claude Design (пиксельно тот же дизайн, но
  компилированный билд — затирается ре-экспортом).

CORS включён. Бэкенд намеренно говорит ключами фронта, поэтому переход с `localStorage`
на API минимален.
