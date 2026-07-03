import os
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
if SERVICE_ACCOUNT_FILE is None:
    raise RuntimeError(
        "Не задана переменная окружения GOOGLE_APPLICATION_CREDENTIALS "
        "(см. ~/.zshrc или .env)."
    )

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

TEMPLATE_SPREADSHEET_ID = "1w8uQB5kV-sm4RwQn9pklil1PVPdCvMwV8dlKlGaySOw"
TARGET_SPREADSHEET_ID = "1bGDO4seSBZSIpQ4OfGC02jq0r8OrHAQCTULhdnd5oa8"

# ─── Настройки ────────────────────────────────────────────────
JUN_TEAMS = 20   # количество команд в лиге JUN (должно быть чётным)
MID_TEAMS = 10   # количество команд в лиге MID (должно быть чётным)
PRO_TEAMS = 8   # количество команд в лиге PRO (должно быть чётным)
# ──────────────────────────────────────────────────────────────


def generate_sheet_names(jun_teams: int, mid_teams: int, pro_teams: int) -> list[str]:
    names = []
    for i in range(1, jun_teams, 2):
        names.append(f"J{i} vs J{i+1}")
    for i in range(1, mid_teams, 2):
        names.append(f"M{i} vs M{i+1}")
    for i in range(1, pro_teams, 2):
        names.append(f"P{i} vs P{i+1}")
    return names


def get_sheet_id_by_title(service, spreadsheet_id, title):
    spreadsheet = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id
    ).execute()
    for sheet in spreadsheet.get("sheets", []):
        props = sheet["properties"]
        if props.get("title") == title:
            return props["sheetId"]
    raise ValueError(f"Лист с названием '{title}' не найден")


def get_existing_sheet_titles(service, spreadsheet_id):
    spreadsheet = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id
    ).execute()
    return {sheet["properties"]["title"] for sheet in spreadsheet.get("sheets", [])}


def main():
    if JUN_TEAMS % 2 != 0 or MID_TEAMS % 2 != 0 or PRO_TEAMS % 2 != 0:
        raise ValueError("Количество команд в каждой лиге должно быть чётным")

    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )
    service = build("sheets", "v4", credentials=creds)

    template_sheet_id = get_sheet_id_by_title(
        service,
        TEMPLATE_SPREADSHEET_ID,
        "template",
    )

    sheet_names = generate_sheet_names(JUN_TEAMS, MID_TEAMS, PRO_TEAMS)
    existing = get_existing_sheet_titles(service, TARGET_SPREADSHEET_ID)

    for sheet_title in sheet_names:
        if sheet_title in existing:
            print(f"Пропущен (уже существует): {sheet_title}")
            continue

        copy_resp = service.spreadsheets().sheets().copyTo(
            spreadsheetId=TEMPLATE_SPREADSHEET_ID,
            sheetId=template_sheet_id,
            body={"destinationSpreadsheetId": TARGET_SPREADSHEET_ID},
        ).execute()

        new_sheet_id = copy_resp["sheetId"]

        service.spreadsheets().batchUpdate(
            spreadsheetId=TARGET_SPREADSHEET_ID,
            body={
                "requests": [{
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": new_sheet_id,
                            "title": sheet_title,
                        },
                        "fields": "title",
                    }
                }]
            },
        ).execute()

        print(f"Создан лист: {sheet_title} (id={new_sheet_id})")


if __name__ == "__main__":
    main()