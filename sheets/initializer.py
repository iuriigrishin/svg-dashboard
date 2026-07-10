"""Стартовые значения нового листа: имена команд-плейсхолдеров, обнулённый счёт
и обнулённые результаты — чтобы свежая игра не унаследовала данные из шаблона.
Ячейки и диапазоны — те же, что читает Code.gs в readSheetData()."""

TEAM1_NAME_CELL = "A2"
TEAM2_NAME_CELL = "A9"
TEAM1_SCORE_CELL = "D16"
TEAM2_SCORE_CELL = "D17"
RESULTS_ROW_1 = "A4:CK4"    # results1 в Code.gs
RESULTS_ROW_2 = "A11:CK11"  # results2 в Code.gs
DATA_COLUMNS = 89           # A:CK


def seed_default_values(
    service,
    spreadsheet_id: str,
    sheet_title: str,
    team1_name: str = "Команда 1",
    team2_name: str = "Команда 2",
) -> None:
    zero_row = [["0"] * DATA_COLUMNS]
    data = [
        {"range": f"'{sheet_title}'!{TEAM1_NAME_CELL}", "values": [[team1_name]]},
        {"range": f"'{sheet_title}'!{TEAM2_NAME_CELL}", "values": [[team2_name]]},
        {"range": f"'{sheet_title}'!{TEAM1_SCORE_CELL}", "values": [[0]]},
        {"range": f"'{sheet_title}'!{TEAM2_SCORE_CELL}", "values": [[0]]},
        {"range": f"'{sheet_title}'!{RESULTS_ROW_1}", "values": zero_row},
        {"range": f"'{sheet_title}'!{RESULTS_ROW_2}", "values": zero_row},
    ]
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"valueInputOption": "USER_ENTERED", "data": data},
    ).execute()
