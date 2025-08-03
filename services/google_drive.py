import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime
from services.photo_upload import drive_service  # уже авторизованный OAuth-доступ

# === Родительская папка на Google Диске (CafeReportsUploads) ===
ROOT_FOLDER_ID = "1LJPZaB7pB1HWNfDf0zg71bJr1on9qsOu"

# === Создание подпапки (например, August), если её нет ===
def get_or_create_month_folder(report_date: str) -> str:
    month_name = report_date.split(".")[1]  # "08" → August
    month_folder_name = datetime.strptime(month_name, "%m").strftime("%B")

    query = (
        f"mimeType='application/vnd.google-apps.folder' "
        f"and name='{month_folder_name}' "
        f"and '{ROOT_FOLDER_ID}' in parents and trashed=false"
    )
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get("files", [])

    if folders:
        return folders[0]["id"]

    folder_metadata = {
        "name": month_folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [ROOT_FOLDER_ID]
    }
    folder = drive_service.files().create(body=folder_metadata, fields="id").execute()
    return folder["id"]

# === Загрузка фото с привязкой к месяцу ===
def upload_photo_with_folder(filepath: str, report_date: str) -> str:
    folder_id = get_or_create_month_folder(report_date)
    filename = os.path.basename(filepath)

    file_metadata = {
        "name": f"{report_date}_отчёт.jpg",
        "parents": [folder_id]
    }
    media = MediaFileUpload(filepath, resumable=True)
    uploaded = drive_service.files().create(
        body=file_metadata, media_body=media, fields="id"
    ).execute()

    # Открываем доступ по ссылке
    drive_service.permissions().create(
        fileId=uploaded["id"],
        body={"role": "reader", "type": "anyone"}
    ).execute()

    file = drive_service.files().get(fileId=uploaded["id"], fields="webViewLink").execute()
    return file["webViewLink"]
