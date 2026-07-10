# SVG Dashboard

Дашборд для двух параллельных матчей: SVG-карта из 43 задач, покрашенная по
результатам из Google Sheets, с live-обновлением.

## Архитектура

```
web/ (браузер)
    → Cloudflare Worker        (кэш + CORS)
        → Apps Script Web App  (читает Google Sheets, отдаёт JSON)
            → Google Sheets    (WORKING_ID)
```

Каждый слой — отдельная папка со своим кодом и своим деплоем:

| Папка | Что деплоит | Чем |
|---|---|---|
| `sheets/` | Листы Google Sheets (копия шаблона + форматирование + стартовые значения) | Sheets API напрямую (Python) |
| `appsscript/` | Backend, который читает таблицу и отдаёт JSON | `clasp` |
| `worker/` | Кэширующий прокси между фронтендом и Apps Script | `wrangler` |
| `web/` | Статический дашборд (GitHub Pages/любой static host) | ничего — просто файлы |

`provision.py` в корне — команда, которая прогоняет все три деплоя по очереди и
сама прописывает получившиеся URL друг другу. Остальное — тонкие модули под
каждую из них, чтобы точечное изменение не требовало трогать всё сразу.

---

## Структура репозитория

```
config.py                # единственный источник ID/настроек — читает .env
provision.py              # sheets → Apps Script → Worker → web/js/config.js, одной командой

sheets/                   # генерация листов Google Sheets с нуля
  auth.py                 # авторизация Sheets API (service account)
  naming.py               # генерация имён листов лиг JUN/MID/PRO — чистая функция
  copier.py                # копирование листа-шаблона, пропуск уже существующих
  formatting.py            # статическое оформление (заморозка шапки, шрифты, ширина колонок)
  conditional_formatting.py # подсветка ячеек с результатом 5/8/12 (условное форматирование)
  initializer.py            # стартовые значения нового листа (имена команд, обнулённый счёт)
  build.py                  # CLI: python -m sheets.build — прогоняет всё по очереди

appsscript/                # backend на Google Apps Script
  src/appsscript.json      # манифест (webapp: execute as me, access: anyone)
  src/Code.gs.tmpl          # исходник Code.gs с плейсхолдерами вместо ID/констант
  deploy.py                 # рендерит Code.gs + clasp push + clasp deploy

worker/                    # Cloudflare Worker (кэш + CORS)
  src/index.js.tmpl         # исходник воркера с плейсхолдером GAS_URL
  wrangler.toml.example     # шаблон конфига (account_id — из .env)
  deploy.py                  # рендерит index.js + wrangler deploy

web/                        # статический фронтенд
  index.html                 # разметка + SVG-карта (43 клетки path-1..path-43)
  css/styles.css             # все стили
  js/config.js                # GAS_URL/POLL_INTERVAL/PAD — правится тут и только тут
  js/paint.js                  # цвет клетки по результату (gold/green/orange/gray) — условное форматирование фронтенда
  js/api.js                    # fetchSheets/fetchSheetData с ретраями
  js/app.js                    # DOM, селектор листов, polling

loadtest/
  locustfile.py             # нагрузка на сам Apps Script (мимо кэша воркера)
  stress_test.py             # нагрузка на Worker, проверяет схему version-poll

tests/
  test_naming.py             # юнит-тест генерации имён листов
```

**Принцип:** каждый файл отвечает за одну вещь. Копирование листа не знает про
цвета, форматирование не знает про стартовые значения, воркер не знает про
Apps Script. Если завтра нужно поменять только цвет подсветки — правится один
файл (`sheets/conditional_formatting.py` или `web/js/paint.js`), а не весь пайплайн.

---

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # заполнить значения (см. ниже)
npm install -g @google/clasp   # если ещё не стоит
clasp login                     # разовая авторизация
# wrangler ставить глобально не обязательно — используется через `npx wrangler`
npx wrangler login               # разовая авторизация
```

Положите service account ключ для Sheets API в `service_account.json` (путь
настраивается через `GOOGLE_APPLICATION_CREDENTIALS` в `.env`).

### `.env` — что заполнить

| Переменная | Где взять |
|---|---|
| `TEMPLATE_SPREADSHEET_ID` / `TARGET_SPREADSHEET_ID` | ID из URL таблицы-шаблона и рабочей таблицы |
| `GOOGLE_APPLICATION_CREDENTIALS` | путь к JSON-ключу сервисного аккаунта |
| `JUN_TEAMS` / `MID_TEAMS` / `PRO_TEAMS` | сколько команд в каждой лиге (чётное число) |
| `ALLOWED_SCORE_VALUES` | какие значения в ячейке счёта = "задача закрыта" |
| `APPSCRIPT_SCRIPT_ID` | Apps Script редактор → Project Settings → Script ID |
| `APPSCRIPT_DEPLOYMENT_ID` | оставить пустым при первом запуске — `provision.py` впишет сам |
| `CF_ACCOUNT_ID` | Cloudflare Dashboard → правая панель на любой странице |

---

## Как запускать

### Всё с нуля одной командой

```bash
python provision.py
```

Создаёт недостающие листы, деплоит Apps Script, деплоит Worker, прописывает
итоговый URL воркера в `web/js/config.js`. Каждый шаг можно пропустить:

```bash
python provision.py --skip-sheets                 # только передеплоить бэкенд
python provision.py --skip-appsscript --skip-worker  # только досоздать листы
```

### По отдельности

```bash
python -m sheets.build              # только листы Google Sheets
python -m appsscript.deploy         # только Apps Script
python -m worker.deploy <exec_url>  # только Worker (нужен exec-URL Apps Script)
```

### Фронтенд

`web/` — статика, открыть `web/index.html` локально или выложить на любой
static hosting (GitHub Pages и т.п.). Единственное, что должно быть актуально —
`GAS_URL` в `web/js/config.js` (провижининг это делает сам).

### Тесты

```bash
pytest tests/
```

### Нагрузочное тестирование

```bash
python loadtest/stress_test.py --users 20 --duration 60 --sheet "J1 vs J2"
locust -f loadtest/locustfile.py --headless -u 30 -r 5 -t 2m --host https://script.google.com
```

Результат `stress_test.py`:
- **ЗЕЛЁНЫЙ** — p95 < 500мс, ошибок нет
- **ЖЁЛТЫЙ** — p95 < 1500мс, терпимо
- **КРАСНЫЙ** — тормозит даже лёгкий запрос — проблема в Apps Script

---

## Что и где менять

| Хочу поменять | Файл |
|---|---|
| Таблицу-шаблон / рабочую таблицу | `.env` (`TEMPLATE_SPREADSHEET_ID` / `TARGET_SPREADSHEET_ID`) |
| Количество команд в лиге | `.env` (`JUN_TEAMS`/`MID_TEAMS`/`PRO_TEAMS`), затем `python -m sheets.build` |
| Какие значения счёта считаются "победой" | `.env` (`ALLOWED_SCORE_VALUES`) — меняет и подсветку в Sheets, и логику Code.gs |
| Статическое оформление новых листов (шрифты, заморозка шапки) | `sheets/formatting.py` |
| Подсветку результата в самой таблице | `sheets/conditional_formatting.py` |
| Стартовые значения нового листа | `sheets/initializer.py` |
| Цвет клетки на карте дашборда | `web/js/paint.js` |
| TTL кэша Apps Script / Worker | `.env` (`APPSCRIPT_CACHE_TTL`, `WORKER_CACHE_TTL`, `WORKER_STALE_TTL`) |
| Логику самого Apps Script (эндпоинты, чтение таблицы) | `appsscript/src/Code.gs.tmpl`, затем `python -m appsscript.deploy` |
| Логику Worker (кэш, CORS) | `worker/src/index.js.tmpl`, затем `python -m worker.deploy <url>` |

---

## Известные ограничения

- **`sheets/conditional_formatting.py`** — это лучшее приближение по смыслу
  (подсветка ячеек со значением из `ALLOWED_SCORE_VALUES`), а не копия
  существующих правил из боевой таблицы: на момент написания не было доступа к
  `service_account.json`, чтобы прочитать реальные правила из UI Google Sheets.
  Проверьте визуально после первого `python -m sheets.build` и подправьте
  диапазон/цвет при необходимости.
- **`onEdit()` в Code.gs вызывает `highlightNeighbors(e)`** — этой функции нет
  в присланном исходнике. Если она объявлена в другом файле вашего Apps Script
  проекта — добавьте его в `appsscript/src/`, иначе `onEdit` будет падать при
  каждом редактировании таблицы.
- **Первый прогон `python provision.py`** создаёт новый Apps Script деплой
  (новый URL). Дальше используется тот же деплой (`APPSCRIPT_DEPLOYMENT_ID`
  сохраняется в `.env` автоматически) — URL не меняется при повторных запусках.
