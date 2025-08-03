from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
import json

def get_drive_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/drive"])
    else:
        raise Exception("❌ Токен не найден. Сначала авторизуй пользователя через client_secrets.json.")
    return build("drive", "v3", credentials=creds)

drive_service = get_drive_service()
