from datetime import datetime
import os
import json
import gspread
from google.oauth2.service_account import Credentials  # ✅ НОВОЕ
from gspread.exceptions import WorksheetNotFound
from config import GSHEET_NAME
import requests

# === Webhook URL для выпадающих статусов
WEBHOOK_URL = "https://script.google.com/macros/s/YOUR_WEBHOOK_ID/exec"

# === Авторизация
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

json_data = os.getenv("GOOGLE_CREDENTIALS_JSON")
if not json_data:
    raise Exception("❌ GOOGLE_CREDENTIALS_JSON не найден!")

try:
    creds_dict = json.loads(json_data)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)  # ✅ фикс
except json.JSONDecodeError:
    raise Exception("❌ GOOGLE_CREDENTIALS_JSON — невалидный JSON!")

client = gspread.authorize(creds)

# === Заголовки таблицы ===
HEADER = ["№", "Дата", "Доход", "7% инвестору", "Ссылка на фото", "Комментарий", "Статус"]

# === Вспомогательная функция для добавления выпадающих статусов ===
def trigger_status_dropdown(sheet_name: str):
    try:
        response = requests.post(WEBHOOK_URL, json={"sheet_name": sheet_name})
        if response.status_code == 200:
            print(f"✅ Webhook выполнен: {response.text}")
        else:
            print(f"❌ Ошибка webhook: {response.status_code} — {response.text}")
    except Exception as e:
        print(f"⚠️ Ошибка при вызове webhook: {e}")

# === Получить или создать лист Google Sheets ===
def get_or_create_sheet(sheet_title: str):
    try:
        sheet = client.open(GSHEET_NAME).worksheet(sheet_title)
    except WorksheetNotFound:
        sheet = client.open(GSHEET_NAME).add_worksheet(title=sheet_title, rows="1000", cols="10")
        sheet.append_row(HEADER)
        sheet.format("A1:G1", {
            "backgroundColor": {"red": 0.7, "green": 0.9, "blue": 0.8},
            "horizontalAlignment": "CENTER",
            "textFormat": {"bold": True}
        })
        trigger_status_dropdown(sheet_title)
    return sheet

# === Добавить отчёт в таблицу ===
def append_to_sheet(date, income, percent, photo_url, comment):
    sheet_title = date_str_to_month(date)
    sheet = get_or_create_sheet(sheet_title)

    all_values = sheet.get_all_values()
    for i, row in enumerate(all_values, start=1):
        if row and row[0].strip().lower() == "итого:":
            sheet.delete_rows(i)
            break

    data_start_row = 2
    next_row_index = len(all_values) + 1 if len(all_values) >= data_start_row else data_start_row

    new_row = [
        str(next_row_index - 1),
        date,
        income,
        percent,
        photo_url,
        comment,
        ""
    ]
    sheet.insert_row(new_row, next_row_index)

    total_row_index = len(sheet.get_all_values()) + 2
    sheet.update(f"A{total_row_index}", [["ИТОГО:"]])
    sheet.update_acell(f"C{total_row_index}", f"=SUM(C2:C{total_row_index - 2})")
    sheet.update_acell(f"D{total_row_index}", f"=SUM(D2:D{total_row_index - 2})")

    sheet.format(f"A{total_row_index}:G{total_row_index}", {
        "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
        "textFormat": {"bold": True},
        "horizontalAlignment": "CENTER"
    })

# === Проверка — был ли уже отчёт за конкретную дату ===
def is_report_already_submitted(date_str: str) -> bool:
    try:
        sheet = client.open(GSHEET_NAME).worksheet(date_str_to_month(date_str))
        data = sheet.get_all_values()
        for row in data[1:]:
            if len(row) > 1 and row[1].strip() == date_str:
                return True
        return False
    except WorksheetNotFound:
        return False

# === Получить месяц из даты (на англ.) ===
def date_str_to_month(date_str: str) -> str:
    date_obj = datetime.strptime(date_str, "%d.%m.%Y")
    return date_obj.strftime("%B")
