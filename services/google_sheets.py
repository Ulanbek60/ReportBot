from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import WorksheetNotFound
from config import GOOGLE_CREDENTIALS_PATH, GSHEET_NAME
import requests

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbx-UZRnOL5oDstXS4bK8dxCXlG5TaCV5BdT-QdH7ncCgaQBA0JYrjfZurWikPVHG5G9kw/exec"

def trigger_status_dropdown(sheet_name: str):
    """
    Вызывает Apps Script webhook для добавления выпадающих статусов на лист Google Sheets
    """
    try:
        response = requests.post(WEBHOOK_URL, json={"sheet_name": sheet_name})
        if response.status_code == 200:
            print(f"✅ Webhook выполнен: {response.text}")
        else:
            print(f"❌ Ошибка webhook: {response.status_code} — {response.text}")
    except Exception as e:
        print(f"⚠️ Ошибка при вызове webhook: {e}")


from google.oauth2.service_account import Credentials
import gspread
from gspread.exceptions import WorksheetNotFound
from config import GOOGLE_CREDENTIALS_PATH, GSHEET_NAME
import requests
from datetime import datetime

scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_file(
    GOOGLE_CREDENTIALS_PATH, scopes=scope
)
client = gspread.authorize(creds)

HEADER = ["№", "Дата", "Доход", "7% инвестору", "Ссылка на фото", "Комментарий", "Статус"]

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
        # 👇 добавляем webhook
        trigger_status_dropdown(sheet_title)

    return sheet

def append_to_sheet(date, income, percent, photo_url, comment):
    sheet_title = date_str_to_month(date)
    sheet = get_or_create_sheet(sheet_title)

    # Удаляем старую строку "ИТОГО:", если есть
    all_values = sheet.get_all_values()
    for i, row in enumerate(all_values, start=1):
        if row and row[0].strip().lower() == "итого:":
            sheet.delete_rows(i)
            break

    values = sheet.get_all_values()
    data_start_row = 2
    next_row_index = len(values) + 1 if len(values) >= data_start_row else data_start_row

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

    # Добавляем строку ИТОГО
    total_row_index = len(sheet.get_all_values()) + 2
    sheet.update(f"A{total_row_index}", [["ИТОГО:"]])
    sheet.update_acell(f"C{total_row_index}", f"=SUM(C2:C{total_row_index - 2})")
    sheet.update_acell(f"D{total_row_index}", f"=SUM(D2:D{total_row_index - 2})")

    sheet.format(f"A{total_row_index}:G{total_row_index}", {
        "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
        "textFormat": {"bold": True},
        "horizontalAlignment": "CENTER"
    })

# 👉 Проверка, отправлялся ли отчёт уже
def is_report_already_submitted(date_str: str) -> bool:
    try:
        sheet = client.open(GSHEET_NAME).worksheet(date_str_to_month(date_str))
        data = sheet.get_all_values()

        for row in data[1:]:  # пропускаем заголовок
            if len(row) > 1 and row[1].strip() == date_str:
                return True
        return False
    except WorksheetNotFound:
        return False  # Если листа ещё нет — отчёт точно не отправлялся

def date_str_to_month(date_str: str) -> str:
    date_obj = datetime.strptime(date_str, "%d.%m.%Y")
    return date_obj.strftime("%B")