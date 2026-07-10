"""Рендерит Code.gs из Code.gs.tmpl + config.py, пушит в Apps Script через clasp
и обновляет веб-деплой. Ничего не знает про Cloudflare Worker — воркер получает
готовый exec-URL уже от provision.py.

    python -m appsscript.deploy

Требования: `clasp login` уже выполнен (npm i -g @google/clasp), и в .env задан
APPSCRIPT_SCRIPT_ID (Project Settings → Script ID в редакторе Apps Script).
Если задан APPSCRIPT_DEPLOYMENT_ID — обновляется тот же деплой (URL не меняется),
иначе clasp создаёт новый и его ID нужно один раз сохранить в .env.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

APPSCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = APPSCRIPT_DIR / "src"
TEMPLATE_FILE = SRC_DIR / "Code.gs.tmpl"
RENDERED_FILE = SRC_DIR / "Code.gs"
CLASP_JSON = APPSCRIPT_DIR / ".clasp.json"


def render_code_gs() -> None:
    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    rendered = (
        template
        .replace("__CACHE_TTL__", str(config.APPSCRIPT_CACHE_TTL))
        .replace("__VERSION_CACHE_TTL__", str(config.APPSCRIPT_VERSION_CACHE_TTL))
        .replace("__TEMPLATE_ID__", config.TEMPLATE_SPREADSHEET_ID)
        .replace("__WORKING_ID__", config.TARGET_SPREADSHEET_ID)
        .replace("__ALLOWED_VALUES__", json.dumps(config.ALLOWED_SCORE_VALUES))
    )
    RENDERED_FILE.write_text(rendered, encoding="utf-8")


def write_clasp_json(script_id: str) -> None:
    CLASP_JSON.write_text(
        json.dumps({"scriptId": script_id, "rootDir": "./src"}, indent=2) + "\n",
        encoding="utf-8",
    )


def run(cmd: list[str]) -> str:
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=APPSCRIPT_DIR, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"Команда {' '.join(cmd)} завершилась с ошибкой")
    return result.stdout


def deploy() -> tuple[str, str, bool]:
    """Возвращает (exec_url, deployment_id, is_new_deployment)."""
    script_id = config.require_appsscript_config()
    write_clasp_json(script_id)
    render_code_gs()

    run(["clasp", "push", "--force"])

    is_new = not config.APPSCRIPT_DEPLOYMENT_ID
    if not is_new:
        run(["clasp", "deploy", "-i", config.APPSCRIPT_DEPLOYMENT_ID, "-d", "provision.py auto-deploy"])
        deployment_id = config.APPSCRIPT_DEPLOYMENT_ID
    else:
        output = run(["clasp", "deploy", "-d", "provision.py auto-deploy"])
        # clasp печатает строку вида "- <deploymentId> @<version>."
        deployment_id = output.strip().splitlines()[-1].split()[1]
        print(f"\nНОВЫЙ ДЕПЛОЙ: {deployment_id} — будет сохранён в .env как APPSCRIPT_DEPLOYMENT_ID\n")

    exec_url = f"https://script.google.com/macros/s/{deployment_id}/exec"
    print(f"Apps Script exec URL: {exec_url}")
    return exec_url, deployment_id, is_new


if __name__ == "__main__":
    deploy()
