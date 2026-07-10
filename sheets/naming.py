"""Генерация имён листов для лиг JUN/MID/PRO. Чистые функции, без обращений к сети."""


def generate_sheet_names(jun_teams: int, mid_teams: int, pro_teams: int) -> list[str]:
    for label, count in (("JUN", jun_teams), ("MID", mid_teams), ("PRO", pro_teams)):
        if count % 2 != 0:
            raise ValueError(f"Количество команд в лиге {label} должно быть чётным (сейчас {count})")

    names = []
    for i in range(1, jun_teams, 2):
        names.append(f"J{i} vs J{i + 1}")
    for i in range(1, mid_teams, 2):
        names.append(f"M{i} vs M{i + 1}")
    for i in range(1, pro_teams, 2):
        names.append(f"P{i} vs P{i + 1}")
    return names
