import os
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Указываем область доступа
SCOPES = ["https://www.googleapis.com/auth/drive"]
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_CREDENTIALS_PATH", "service_account.json")
ROOT_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")  # 📁 ID папки "CafeReportsUploads"

# Авторизация
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build("drive", "v3", credentials=creds)

def get_or_create_month_folder(report_date: str) -> str:
    dt = datetime.strptime(report_date, "%d.%m.%Y")
    month_name = dt.strftime("%B")

    # Поиск папки внутри корневой
    query = (
        f"mimeType='application/vnd.google-apps.folder' and "
        f"name='{month_name}' and '{ROOT_FOLDER_ID}' in parents and trashed=false"
    )
    response = drive_service.files().list(q=query, fields="files(id)").execute()
    folders = response.get("files", [])

    if folders:
        return folders[0]["id"]

    # Создание подпапки, если нет
    metadata = {
        "name": month_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [ROOT_FOLDER_ID]
    }
    folder = drive_service.files().create(body=metadata, fields="id").execute()
    return folder["id"]

def upload_photo_to_drive(photo_path: str, report_date: str) -> str:
    folder_id = get_or_create_month_folder(report_date)
    timestamp = datetime.now().strftime("%H-%M-%S")
    filename = f"{report_date}_отчёт_{timestamp}.jpg"

    file_metadata = {
        "name": filename,
        "parents": [folder_id]
    }

    media = MediaFileUpload(photo_path, resumable=True)
    uploaded = drive_service.files().create(
        body=file_metadata, media_body=media, fields="id"
    ).execute()

    # Делаем файл публичным
    drive_service.permissions().create(
        fileId=uploaded["id"],
        body={"role": "reader", "type": "anyone"},
    ).execute()

    # Получаем ссылку
    file = drive_service.files().get(
        fileId=uploaded["id"], fields="webViewLink"
    ).execute()

    return file["webViewLink"]
