"""
Единственный источник правды для всех ID, кредов и настроек проекта.
Всё остальное (sheets/, appsscript/, worker/) читает значения только отсюда —
чтобы поменять таблицу-шаблон, размер лиги или TTL кэша, правишь один файл (.env).
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def _env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


def _require(name: str) -> str:
    value = _env(name)
    if not value:
        raise RuntimeError(f"Не задана переменная окружения {name} (см. .env.example)")
    return value


# ── Google Sheets ────────────────────────────────────────────────
TEMPLATE_SPREADSHEET_ID = _env("TEMPLATE_SPREADSHEET_ID", "1w8uQB5kV-sm4RwQn9pklil1PVPdCvMwV8dlKlGaySOw")
TARGET_SPREADSHEET_ID = _env("TARGET_SPREADSHEET_ID", "1bGDO4seSBZSIpQ4OfGC02jq0r8OrHAQCTULhdnd5oa8")
GOOGLE_APPLICATION_CREDENTIALS = _env("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")

JUN_TEAMS = int(_env("JUN_TEAMS", "20"))
MID_TEAMS = int(_env("MID_TEAMS", "10"))
PRO_TEAMS = int(_env("PRO_TEAMS", "8"))

# Значения в ячейке счёта, которые считаются "задача закрыта" — используются и
# в sheets/conditional_formatting.py (подсветка в таблице), и в шаблоне Code.gs
# (appsscript/src/Code.gs.tmpl) — один список на оба места.
ALLOWED_SCORE_VALUES = [v.strip() for v in _env("ALLOWED_SCORE_VALUES", "5,8,12").split(",")]


# ── Apps Script (clasp) ──────────────────────────────────────────
APPSCRIPT_SCRIPT_ID = _env("APPSCRIPT_SCRIPT_ID")
APPSCRIPT_DEPLOYMENT_ID = _env("APPSCRIPT_DEPLOYMENT_ID")  # пусто → clasp создаст новый деплой
APPSCRIPT_CACHE_TTL = int(_env("APPSCRIPT_CACHE_TTL", "60"))          # сек, кэш листа/данных
APPSCRIPT_VERSION_CACHE_TTL = int(_env("APPSCRIPT_VERSION_CACHE_TTL", "30"))  # сек, кэш version-эндпоинта


def require_appsscript_config() -> str:
    return _require("APPSCRIPT_SCRIPT_ID")


# ── Cloudflare Worker (wrangler) ─────────────────────────────────
CF_ACCOUNT_ID = _env("CF_ACCOUNT_ID")
CF_WORKER_NAME = _env("CF_WORKER_NAME", "blue-shape-5fbb")
WORKER_CACHE_TTL = int(_env("WORKER_CACHE_TTL", "5"))     # сек, свежий кэш
WORKER_STALE_TTL = int(_env("WORKER_STALE_TTL", "60"))    # сек, устаревший кэш пока обновляется

# Публичный адрес задеплоенного Worker'а — то, что фронтенд (web/js/config.js)
# и нагрузочные тесты (loadtest/) используют как GAS_URL. provision.py
# перезаписывает эту переменную в .env после каждого деплоя воркера.
WORKER_URL = _env("WORKER_URL", "https://blue-shape-5fbb.iurkagrishin187.workers.dev")


def require_worker_config() -> str:
    return _require("CF_ACCOUNT_ID")


def appscript_exec_url() -> str | None:
    if not APPSCRIPT_DEPLOYMENT_ID:
        return None
    return f"https://script.google.com/macros/s/{APPSCRIPT_DEPLOYMENT_ID}/exec"


def persist_env(name: str, value: str) -> None:
    """Обновляет (или добавляет) NAME=value в .env — так provision.py запоминает
    APPSCRIPT_DEPLOYMENT_ID/WORKER_URL между запусками, не создавая лишних деплоев."""
    env_path = ROOT / ".env"
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []

    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{name}=") or line.startswith(f"{name} ="):
            lines[i] = f"{name}={value}"
            found = True
            break
    if not found:
        lines.append(f"{name}={value}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ[name] = value  # чтобы текущий процесс тоже увидел новое значение
