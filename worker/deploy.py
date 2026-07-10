"""Рендерит src/index.js из index.js.tmpl + config.py (и exec-URL от appsscript/deploy.py),
затем разворачивает Worker через `npx wrangler deploy`.

    python -m worker.deploy https://script.google.com/macros/s/XXX/exec

Требования: `npx wrangler login` уже выполнен (или задан CLOUDFLARE_API_TOKEN в
окружении), и в .env задан CF_ACCOUNT_ID.
"""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

WORKER_DIR = Path(__file__).resolve().parent
SRC_DIR = WORKER_DIR / "src"
TEMPLATE_FILE = SRC_DIR / "index.js.tmpl"
RENDERED_FILE = SRC_DIR / "index.js"
WRANGLER_TOML = WORKER_DIR / "wrangler.toml"
WRANGLER_EXAMPLE = WORKER_DIR / "wrangler.toml.example"


def render_index_js(gas_url: str) -> None:
    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    rendered = (
        template
        .replace("__GAS_URL__", gas_url)
        .replace("__CACHE_TTL__", str(config.WORKER_CACHE_TTL))
        .replace("__STALE_TTL__", str(config.WORKER_STALE_TTL))
    )
    RENDERED_FILE.write_text(rendered, encoding="utf-8")


def write_wrangler_toml() -> None:
    account_id = config.require_worker_config()
    example = WRANGLER_EXAMPLE.read_text(encoding="utf-8")
    rendered = re.sub(
        r'account_id = ".*"',
        f'account_id = "{account_id}"',
        example,
    ).replace('name = "blue-shape-5fbb"', f'name = "{config.CF_WORKER_NAME}"')
    WRANGLER_TOML.write_text(rendered, encoding="utf-8")


def run(cmd: list[str]) -> str:
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=WORKER_DIR, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"Команда {' '.join(cmd)} завершилась с ошибкой")
    return result.stdout + result.stderr


def deploy(gas_url: str) -> str:
    """Возвращает публичный URL Worker'а."""
    write_wrangler_toml()
    render_index_js(gas_url)

    output = run(["npx", "wrangler", "deploy"])
    match = re.search(r"https://\S+\.workers\.dev\S*", output)
    worker_url = match.group(0) if match else config.WORKER_URL
    print(f"Worker URL: {worker_url}")
    return worker_url


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Использование: python -m worker.deploy <gas_exec_url>")
    deploy(sys.argv[1])
