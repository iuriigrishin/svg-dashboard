"""
stress_test.py — тест diff-схемы: version poll каждые 2с + полные данные только при изменении
"""
import asyncio
import argparse
import time
import statistics
from dataclasses import dataclass, field
import aiohttp

GAS_URL = "https://blue-shape-5fbb.iurkagrishin187.workers.dev"
VERSION_POLL   = 2    # секунд — как в новом index.html


@dataclass
class Stats:
    version_latencies: list = field(default_factory=list)
    full_latencies:    list = field(default_factory=list)
    errors:   int = 0
    timeouts: int = 0

    def report(self, users, duration):
        total = len(self.version_latencies) + self.errors + self.timeouts
        print("\n" + "═" * 60)
        print(f"  РЕЗУЛЬТАТЫ  |  {users} пользователей, {duration}с")
        print("═" * 60)
        print(f"  Запросов версии  : {len(self.version_latencies)}")
        print(f"  Запросов данных  : {len(self.full_latencies)}")
        print(f"  Ошибок           : {self.errors}")
        print(f"  Таймаутов        : {self.timeouts}")

        if self.version_latencies:
            s = sorted(self.version_latencies)
            print(f"\n  Latency VERSION (лёгкий запрос, мс):")
            print(f"    median = {statistics.median(s):.0f}")
            print(f"    p95    = {s[int(len(s)*0.95)]:.0f}")
            print(f"    max    = {s[-1]:.0f}")

        if self.full_latencies:
            s = sorted(self.full_latencies)
            print(f"\n  Latency FULL DATA (тяжёлый запрос, мс):")
            print(f"    median = {statistics.median(s):.0f}")
            print(f"    p95    = {s[int(len(s)*0.95)]:.0f}")
            print(f"    max    = {s[-1]:.0f}")

        print(f"\n  RPS (реальный)   : {total / duration:.2f}")
        print("═" * 60)

        if self.version_latencies:
            p95v = sorted(self.version_latencies)[int(len(self.version_latencies)*0.95)]
            print()
            if p95v < 500 and self.errors == 0:
                print("  ЗЕЛЁНЫЙ: diff работает отлично, сайт обновляется быстро")
            elif p95v < 1500:
                print("  ЖЁЛТЫЙ: version-запрос медленноват, но терпимо")
            else:
                print("  КРАСНЫЙ: даже лёгкий запрос тормозит — проблема в GAS")
        print()


stats = Stats()


async def simulated_browser(session, sheet_name, duration, user_id):
    """Эмулирует новый index.html: каждые 2с проверяет версию, при изменении тянет данные."""
    deadline = time.monotonic() + duration
    await asyncio.sleep(user_id * 0.07)
    known_version = None

    while time.monotonic() < deadline:
        # Шаг 1: лёгкий запрос версии
        url_v = f"{GAS_URL}?action=version&sheet={sheet_name}"
        t0 = time.monotonic()
        try:
            async with session.get(url_v, timeout=aiohttp.ClientTimeout(total=10),
                                   allow_redirects=True) as resp:
                data = await resp.json(content_type=None)
                ms = (time.monotonic() - t0) * 1000
                stats.version_latencies.append(ms)
                version = data.get('version')

                # Шаг 2: версия изменилась — тянем полные данные
                if version and version != known_version:
                    url_f = f"{GAS_URL}?sheet={sheet_name}"
                    t1 = time.monotonic()
                    async with session.get(url_f, timeout=aiohttp.ClientTimeout(total=15),
                                           allow_redirects=True) as resp2:
                        await resp2.json(content_type=None)
                        ms2 = (time.monotonic() - t1) * 1000
                        stats.full_latencies.append(ms2)
                        known_version = version
                        print(f"  user={user_id:>3}  VERSION CHANGED → full {ms2:.0f}ms   ", end="\r")
                else:
                    print(f"  user={user_id:>3}  version ok {ms:.0f}ms              ", end="\r")

        except asyncio.TimeoutError:
            stats.timeouts += 1
        except Exception as e:
            stats.errors += 1
            print(f"  user={user_id:>3}  ERR {e}        ", end="\r")

        await asyncio.sleep(VERSION_POLL)


async def run_sheets_list(session):
    url = f"{GAS_URL}?action=sheets"
    t0  = time.monotonic()
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10),
                               allow_redirects=True) as resp:
            data = await resp.json(content_type=None)
            ms = (time.monotonic() - t0) * 1000
            print(f"  [sheets] ответ за {ms:.0f} мс → {data}")
            return data
    except Exception as e:
        print(f"  [sheets] ОШИБКА: {e}")
        return ["Game 1"]


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--users",    type=int, default=20)
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--sheet",    type=str, default=None)
    args = parser.parse_args()

    connector = aiohttp.TCPConnector(limit=args.users + 5)
    async with aiohttp.ClientSession(connector=connector) as session:
        print("  Получаем список листов...")
        sheets = await run_sheets_list(session)
        sheet  = args.sheet or sheets[0]
        print(f"  Тестируем лист: «{sheet}»")
        print(f"  Запускаем {args.users} виртуальных браузеров на {args.duration}с...\n")
        print("  (пока тест идёт — измени что-нибудь в таблице, увидишь VERSION CHANGED)\n")

        tasks = [
            simulated_browser(session, sheet, args.duration, i)
            for i in range(args.users)
        ]
        await asyncio.gather(*tasks)

    stats.report(args.users, args.duration)


if __name__ == "__main__":
    asyncio.run(main())