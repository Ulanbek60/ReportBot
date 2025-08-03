
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
INVESTOR_ID = int(os.getenv("INVESTOR_ID"))

GSHEET_NAME = os.getenv("GSHEET_NAME")
GSHEET_TAB = os.getenv("GSHEET_TAB")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")