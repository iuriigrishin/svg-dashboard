"""Копирование листа-шаблона в рабочую таблицу. Ничего не знает про форматирование
или стартовые значения — только про то, какие листы существуют и как их создать."""


def get_sheet_id_by_title(service, spreadsheet_id: str, title: str) -> int:
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in spreadsheet.get("sheets", []):
        props = sheet["properties"]
        if props.get("title") == title:
            return props["sheetId"]
    raise ValueError(f"Лист с названием '{title}' не найден")


def get_existing_sheet_titles(service, spreadsheet_id: str) -> set[str]:
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    return {sheet["properties"]["title"] for sheet in spreadsheet.get("sheets", [])}


def copy_missing_sheets(
    service,
    template_id: str,
    target_id: str,
    sheet_names: list[str],
    template_tab: str = "template",
) -> list[tuple[str, int]]:
    """Копирует лист `template_tab` из template_id в target_id под каждым именем из
    sheet_names, пропуская те, что уже существуют. Возвращает [(имя, sheetId), ...]
    для реально скопированных листов."""
    template_sheet_id = get_sheet_id_by_title(service, template_id, template_tab)
    existing = get_existing_sheet_titles(service, target_id)

    created = []
    for sheet_title in sheet_names:
        if sheet_title in existing:
            print(f"Пропущен (уже существует): {sheet_title}")
            continue

        copy_resp = service.spreadsheets().sheets().copyTo(
            spreadsheetId=template_id,
            sheetId=template_sheet_id,
            body={"destinationSpreadsheetId": target_id},
        ).execute()
        new_sheet_id = copy_resp["sheetId"]

        service.spreadsheets().batchUpdate(
            spreadsheetId=target_id,
            body={
                "requests": [{
                    "updateSheetProperties": {
                        "properties": {"sheetId": new_sheet_id, "title": sheet_title},
                        "fields": "title",
                    }
                }]
            },
        ).execute()

        print(f"Создан лист: {sheet_title} (id={new_sheet_id})")
        created.append((sheet_title, new_sheet_id))

    return created
