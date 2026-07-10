"""CLI-оркестратор: собирает недостающие листы рабочей таблицы с нуля.

    python -m sheets.build                  # все шаги для всех недостающих листов
    python -m sheets.build --skip-init       # без заполнения стартовых значений
    python -m sheets.build --skip-format     # без статического форматирования и подсветки

Каждый шаг (copier / formatting / conditional_formatting / initializer) можно
менять независимо — build.py только вызывает их по очереди.
"""
import argparse

import config
from sheets import auth, conditional_formatting, copier, formatting, initializer, naming


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-format", action="store_true", help="не применять formatting.py/conditional_formatting.py")
    parser.add_argument("--skip-init", action="store_true", help="не заполнять стартовые значения (initializer.py)")
    args = parser.parse_args()

    service = auth.get_sheets_service()

    sheet_names = naming.generate_sheet_names(config.JUN_TEAMS, config.MID_TEAMS, config.PRO_TEAMS)
    created = copier.copy_missing_sheets(
        service, config.TEMPLATE_SPREADSHEET_ID, config.TARGET_SPREADSHEET_ID, sheet_names,
    )

    if not created:
        print("Новых листов нет — всё уже создано.")
        return

    for sheet_title, sheet_id in created:
        if not args.skip_format:
            formatting.apply_static_formatting(service, config.TARGET_SPREADSHEET_ID, sheet_id)
            conditional_formatting.apply_score_highlighting(service, config.TARGET_SPREADSHEET_ID, sheet_id)
        if not args.skip_init:
            initializer.seed_default_values(service, config.TARGET_SPREADSHEET_ID, sheet_title)
        print(f"Готово: {sheet_title}")


if __name__ == "__main__":
    main()
