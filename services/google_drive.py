import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === Авторизация
scope = ["https://www.googleapis.com/auth/drive"]
json_data = os.getenv("GOOGLE_CREDENTIALS_JSON")

if json_data:
    creds_dict = json.loads(json_data)
else:
    with open("google_credentials.json") as f:
        creds_dict = json.load(f)

creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
drive_service = build("drive", "v3", credentials=creds)

# === Создание папки по названию (месяц)
def get_or_create_month_folder(name: str) -> str:
    query = f"mimeType='application/vnd.google-apps.folder' and name='{name}' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get("files", [])

    if folders:
        return folders[0]["id"]

    folder_metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    folder = drive_service.files().create(body=folder_metadata, fields="id").execute()
    return folder["id"]

# === Загрузка фото в Google Drive + получение ссылки
def upload_photo_with_folder(filepath: str, report_date: str) -> str:
    folder_name = report_date.split(".")[1]  # месяц (например, "08")
    folder_id = get_or_create_month_folder(folder_name)
    filename = f"{report_date}_отчёт.jpg"

    file_metadata = {"name": filename, "parents": [folder_id]}
    media = MediaFileUpload(filepath, resumable=True)
    uploaded = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()

    # Сделать файл общедоступным
    drive_service.permissions().create(
        fileId=uploaded["id"],
        body={"role": "reader", "type": "anyone"}
    ).execute()

    file = drive_service.files().get(fileId=uploaded["id"], fields="webViewLink").execute()
    return file["webViewLink"]
