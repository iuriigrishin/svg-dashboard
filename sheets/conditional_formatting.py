"""Условное форматирование результатов: подсвечивает ячейку, если её значение
входит в config.ALLOWED_SCORE_VALUES — то есть задача считается закрытой (та же
логика, что читает Code.gs в readSheetData()/`allowed`, и что красит клетки карты
в web/js/paint.js). Ряды и диапазон колонок взяты из Code.gs: getRange("A1:CK11"),
results1 = строка 4, results2 = строка 11.

NOTE: у меня нет доступа к боевой таблице-шаблону, поэтому здесь — лучшее
приближение по смыслу, а не копия существующих правил. Проверьте визуально после
первого запуска и подправьте диапазоны/цвет при необходимости."""

import config

RESULT_ROWS = (3, 10)          # 0-based индексы строк 4 и 11
DATA_START_COL = 0             # колонка A
DATA_END_COL = 89              # колонка CK (эксклюзивно), см. Code.gs "A1:CK11"
HIGHLIGHT_COLOR = {"red": 0.72, "green": 0.88, "blue": 0.72}  # светло-зелёный


def _formula_for_row(row_1based: int, allowed_values: list[str]) -> str:
    conditions = ",".join(f'A{row_1based}="{v}"' for v in allowed_values)
    return f"=OR({conditions})"


def apply_score_highlighting(service, spreadsheet_id: str, sheet_id: int) -> None:
    requests = []
    for row_index in RESULT_ROWS:
        requests.append({
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sheet_id,
                        "startRowIndex": row_index,
                        "endRowIndex": row_index + 1,
                        "startColumnIndex": DATA_START_COL,
                        "endColumnIndex": DATA_END_COL,
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "CUSTOM_FORMULA",
                            "values": [{
                                "userEnteredValue": _formula_for_row(
                                    row_index + 1, config.ALLOWED_SCORE_VALUES
                                )
                            }],
                        },
                        "format": {"backgroundColor": HIGHLIGHT_COLOR},
                    },
                },
                "index": 0,
            }
        })

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests},
    ).execute()
