# google_drive.py — обновлённый с поддержкой даты отчёта

from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
import config
import os

# Настройка клиента Google Drive
SCOPES = ["https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(
    config.GOOGLE_CREDENTIALS_PATH, scopes=SCOPES
)
drive_service = build("drive", "v3", credentials=creds)

def get_or_create_month_folder(report_date: str):
    dt = datetime.strptime(report_date, "%d.%m.%Y")
    folder_name = dt.strftime("%B").capitalize()

    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
    results = (
        drive_service.files()
        .list(q=query, spaces="drive", fields="files(id, name)")
        .execute()
    )
    folders = results.get("files", [])

    if folders:
        return folders[0]["id"]

    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = drive_service.files().create(body=file_metadata, fields="id").execute()
    return folder["id"]

def upload_photo_with_folder(filepath: str, report_date: str) -> str:
    folder_id = get_or_create_month_folder(report_date)
    filename = os.path.basename(filepath)

    file_metadata = {"name": f"{report_date}_отчёт.jpg", "parents": [folder_id]}
    media = MediaFileUpload(filepath, resumable=True)
    uploaded = (
        drive_service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )

    drive_service.permissions().create(
        fileId=uploaded["id"], body={"role": "reader", "type": "anyone"}
    ).execute()

    file = drive_service.files().get(fileId=uploaded["id"], fields="webViewLink").execute()
    return file["webViewLink"]
