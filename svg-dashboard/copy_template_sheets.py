# copy_template_sheets.py

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
TARGET_SPREADSHEET_ID = "14b-zVslMP_UUq55lAxC5xNEzjT5t8IUxFdN-8r2a2gU"

names = {
    1: "Game 4",
    2: "Game 5",
    3: "Game 6",
}

def get_sheet_id_by_title(service, spreadsheet_id, title):
    spreadsheet = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id
    ).execute()
    for sheet in spreadsheet.get("sheets", []):
        props = sheet["properties"]
        if props.get("title") == title:
            return props["sheetId"]
    raise ValueError(f"Лист с названием '{title}' не найден")

def main():
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

    for key, sheet_title in names.items():
        copy_body = {
            "destinationSpreadsheetId": TARGET_SPREADSHEET_ID
        }
        copy_resp = service.spreadsheets().sheets().copyTo(
            spreadsheetId=TEMPLATE_SPREADSHEET_ID,
            sheetId=template_sheet_id,
            body=copy_body,
        ).execute()

        new_sheet_id = copy_resp["sheetId"]

        batch_body = {
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": new_sheet_id,
                            "title": sheet_title,
                        },
                        "fields": "title",
                    }
                }
            ]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=TARGET_SPREADSHEET_ID,
            body=batch_body,
        ).execute()

        print(f"Создан лист: {sheet_title} (id={new_sheet_id})")

if __name__ == "__main__":
    main()
