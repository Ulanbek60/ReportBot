# Пример конфигурации — реальные значения берутся из .env

from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")             # example: '123456:ABC-DEF...'
OWNER_ID = int(os.getenv("OWNER_ID"))          # example: 123456789
INVESTOR_ID = int(os.getenv("INVESTOR_ID"))    # example: 987654321

GSHEET_NAME = os.getenv("GSHEET_NAME")         # example: 'Cafe Reports'
GSHEET_TAB = os.getenv("GSHEET_TAB")           # example: 'August'
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")  # example: 'google_credentials.json'
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")    # example: '1ABCDEFxyz...'
