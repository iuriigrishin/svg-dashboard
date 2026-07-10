"""Главная команда: поднимает всю цепочку с нуля для новой/текущей рабочей таблицы.

    python provision.py                    # sheets → Apps Script → Worker → фронтенд
    python provision.py --skip-sheets      # только передеплоить Apps Script + Worker
    python provision.py --skip-worker      # не трогать Cloudflare (например, нет wrangler login)

Каждый шаг — отдельный модуль (sheets/build.py, appsscript/deploy.py,
worker/deploy.py), provision.py только вызывает их по очереди и передаёт между
ними результат (exec-URL Apps Script → GAS_URL воркера → config.js фронтенда).
"""
import argparse
import re
import sys
from pathlib import Path

import config

WEB_CONFIG_JS = Path(__file__).resolve().parent / "web" / "js" / "config.js"


def patch_frontend_config(worker_url: str) -> None:
    text = WEB_CONFIG_JS.read_text(encoding="utf-8")
    patched = re.sub(
        r"const GAS_URL = '.*?';",
        f"const GAS_URL = '{worker_url}';",
        text,
    )
    WEB_CONFIG_JS.write_text(patched, encoding="utf-8")
    print(f"Обновлён {WEB_CONFIG_JS.relative_to(Path.cwd())}: GAS_URL = {worker_url}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skip-sheets", action="store_true", help="не создавать/форматировать листы Google Sheets")
    parser.add_argument("--skip-appsscript", action="store_true", help="не пушить/деплоить Apps Script")
    parser.add_argument("--skip-worker", action="store_true", help="не деплоить Cloudflare Worker")
    args = parser.parse_args()

    if not args.skip_sheets:
        from sheets import build as sheets_build
        sys.argv = [sys.argv[0]]  # sheets.build.main() тоже парсит argv — не мешаем ему
        sheets_build.main()

    exec_url = config.appscript_exec_url()
    if not args.skip_appsscript:
        from appsscript import deploy as appsscript_deploy
        exec_url, deployment_id, is_new = appsscript_deploy.deploy()
        if is_new:
            config.persist_env("APPSCRIPT_DEPLOYMENT_ID", deployment_id)
    elif not exec_url:
        sys.exit("Нет APPSCRIPT_DEPLOYMENT_ID в .env и --skip-appsscript — неоткуда взять exec-URL")

    worker_url = config.WORKER_URL
    if not args.skip_worker:
        from worker import deploy as worker_deploy
        worker_url = worker_deploy.deploy(exec_url)
        config.persist_env("WORKER_URL", worker_url)
        patch_frontend_config(worker_url)

    print("\nГотово.")
    print(f"  Apps Script exec URL : {exec_url}")
    print(f"  Worker URL           : {worker_url}")


if __name__ == "__main__":
    main()
