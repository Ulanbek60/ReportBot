import os
from datetime import datetime
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def upload_photo_to_drive(photo_path: str, report_date: str) -> str:
    # Авторизация
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.json")

    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()

    gauth.SaveCredentialsFile("credentials.json")
    drive = GoogleDrive(gauth)

    # Получаем месяц из report_date
    dt = datetime.strptime(report_date, "%d.%m.%Y")
    month_name = dt.strftime("%B")  # Например: August

    # Ищем/создаем корневую папку
    root_folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

    # Ищем/создаем подпапку по месяцу в корневой папке
    folder_id = None
    folder_list = drive.ListFile({
        'q': f"title='{month_name}' and mimeType='application/vnd.google-apps.folder' and '{root_folder_id}' in parents and trashed=false"
    }).GetList()

    if folder_list:
        folder_id = folder_list[0]['id']
    else:
        folder_metadata = {
            'title': month_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [{'id': root_folder_id}]
        }
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        folder_id = folder['id']

    # Формируем имя файла по report_date с точным временем для уникальности
    timestamp = datetime.now().strftime("%H-%M-%S")
    file_title = f"{report_date}_отчёт_{timestamp}.jpg"

    file = drive.CreateFile({
        'title': file_title,
        'parents': [{'id': folder_id}]
    })
    file.SetContentFile(photo_path)
    file.Upload()

    file.InsertPermission({
        'type': 'anyone',
        'value': 'anyone',
        'role': 'reader'
    })

    return file['alternateLink']