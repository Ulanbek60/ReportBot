import os
from datetime import datetime
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def upload_photo_to_drive(photo_path: str, report_date: str) -> str:
    # 🔐 Авторизация через OAuth2
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.json")

    if gauth.credentials is None:
        gauth.LocalWebserverAuth()  # первый запуск
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()

    gauth.SaveCredentialsFile("credentials.json")
    drive = GoogleDrive(gauth)

    # 🗂️ Название месяца
    dt = datetime.strptime(report_date, "%d.%m.%Y")
    month_name = dt.strftime("%B")

    # 📁 Корневая папка (ID из .env)
    root_folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    if not root_folder_id:
        raise ValueError("Переменная GOOGLE_DRIVE_FOLDER_ID не установлена")

    # 🔍 Проверяем/создаём папку по месяцу
    folder_id = None
    folder_list = drive.ListFile({
        'q': f"title='{month_name}' and mimeType='application/vnd.google-apps.folder' "
             f"and '{root_folder_id}' in parents and trashed=false"
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

    # 📸 Загружаем фото
    timestamp = datetime.now().strftime("%H-%M-%S")
    file_title = f"{report_date}_отчёт_{timestamp}.jpg"

    file = drive.CreateFile({
        'title': file_title,
        'parents': [{'id': folder_id}]
    })
    file.SetContentFile(photo_path)
    file.Upload()

    # 🌍 Делаем ссылку публичной
    file.InsertPermission({
        'type': 'anyone',
        'value': 'anyone',
        'role': 'reader'
    })

    return file['alternateLink']

