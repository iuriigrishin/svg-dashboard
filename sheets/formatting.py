"""Статическое оформление ячеек: то, что не зависит от игровых данных
(шрифты, заморозка шапки, ширина колонок). Цвет по результату — в
conditional_formatting.py, стартовые значения — в initializer.py."""

HEADER_ROW = 0       # строка 1 (0-based) — номера задач
LABEL_COLUMN = 0     # колонка A — имена команд


def apply_static_formatting(service, spreadsheet_id: str, sheet_id: int) -> None:
    requests = [
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {"frozenRowCount": 1, "frozenColumnCount": 1},
                },
                "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": HEADER_ROW,
                    "endRowIndex": HEADER_ROW + 1,
                },
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat.textFormat.bold",
            }
        },
        {
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": LABEL_COLUMN,
                    "endIndex": LABEL_COLUMN + 1,
                },
                "properties": {"pixelSize": 140},
                "fields": "pixelSize",
            }
        },
    ]
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests},
    ).execute()
