import os
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_photo_to_drive(photo_path: str, report_date: str) -> str:
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'service_account.json'
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    drive_service = build('drive', 'v3', credentials=credentials)

    # Корневая папка из .env
    parent_folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

    # Получаем название месяца
    dt = datetime.strptime(report_date, "%d.%m.%Y")
    month_name = dt.strftime("%B")

    # Проверка наличия подпапки по месяцу
    query = f"name='{month_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_folder_id}' in parents and trashed=false"
    response = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = response.get('files', [])

    if files:
        folder_id = files[0]['id']
    else:
        file_metadata = {
            'name': month_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = drive_service.files().create(body=file_metadata, fields='id').execute()
        folder_id = folder.get('id')

    # Загружаем фото
    timestamp = datetime.now().strftime("%H-%M-%S")
    file_name = f"{report_date}_отчёт_{timestamp}.jpg"
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }

    media = MediaFileUpload(photo_path, mimetype='image/jpeg')
    uploaded = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id,webViewLink',
        supportsAllDrives=True
    ).execute()

    # Делаем файл публичным
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }
    drive_service.permissions().create(
        fileId=uploaded['id'],
        body=permission
    ).execute()

    return uploaded['webViewLink']
