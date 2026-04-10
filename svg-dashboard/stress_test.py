"""
locustfile.py — Locust-тест GAS-эндпоинта + эмуляция записи
Запуск:
  locust -f locustfile.py --headless -u 30 -r 5 -t 2m --host https://script.google.com
  locust -f locustfile.py          # веб-интерфейс на http://localhost:8089
"""
import random
from locust import HttpUser, task, between, events

GAS_PATH = (
    "/macros/s/"
    "AKfycbwsk7ECJf3gQaz0nbxhnRQ_0b4slJ2gWjE9Tv54gJDIL6tZTIYiYj5383KDDYZxOWWUZQ"
    "/exec"
)
SHEETS = ["Game 1", "Game 2", "Game 3", "Game 4", "Game 5"]


class DashboardViewer(HttpUser):
    """
    Обычный зритель — браузер с открытым index.html.
    Делает poll каждые 5 секунд (wait_time эмулирует это).
    """
    wait_time = between(4, 6)

    def on_start(self):
        self.sheet = random.choice(SHEETS)
        self.client.get(f"{GAS_PATH}?action=sheets", name="[GET] sheets list")

    @task(10)
    def poll_sheet(self):
        self.client.get(
            f"{GAS_PATH}?sheet={self.sheet}",
            name="[GET] sheet data",
        )

    @task(1)
    def switch_sheet(self):
        self.sheet = random.choice(SHEETS)
        self.client.get(
            f"{GAS_PATH}?sheet={self.sheet}",
            name="[GET] sheet data (switch)",
        )


class DashboardEditor(HttpUser):
    """
    Редактор — записывает результат задачи.
    Если doPost не реализован в GAS — запросы вернут 405, это тоже информативно.
    """
    wait_time = between(10, 30)

    def on_start(self):
        self.sheet = random.choice(SHEETS)

    @task
    def write_cell(self):
        square = random.randint(1, 43)
        payload = {
            "sheet":  self.sheet,
            "square": square,
            "team":   random.choice(["team1", "team2"]),
            "value":  random.choice([True, False]),
        }
        with self.client.post(
            GAS_PATH,
            json=payload,
            name="[POST] write cell",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 302, 405):
                resp.success()
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")


@events.quitting.add_listener
def on_quit(environment, **kw):
    stats = environment.stats
    total = stats.total
    print("\n" + "=" * 55)
    print("  ИТОГ LOCUST-ТЕСТА")
    print("=" * 55)
    for name, entry in stats.entries.items():
        p95 = entry.get_response_time_percentile(0.95)
        print(
            f"  {name[1]:<30} "
            f"rps={entry.current_rps:>6.1f}  "
            f"p95={p95:>6}мс  "
            f"fail={entry.num_failures}"
        )
    fail_ratio = total.num_failures / total.num_requests if total.num_requests else 0
    p95_total  = total.get_response_time_percentile(0.95)
    print()
    if p95_total < 2000 and fail_ratio < 0.05:
        print("  САЙТ выдержит нагрузку")
    elif p95_total < 5000 and fail_ratio < 0.15:
        print("  Приемлемо, но GAS начинает тормозить")
    else:
        print("  GAS не справляется — будут зависания на сайте")
    print("=" * 55 + "\n")