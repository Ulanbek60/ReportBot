import os
import json
from google.oauth2.service_account import Credentials


def get_google_credentials(scopes: list) -> Credentials:
    json_data = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not json_data:
        raise ValueError("❌ GOOGLE_CREDENTIALS_JSON not set in environment")

    creds_dict = json.loads(json_data)

    # Обязательно превращаем \\n → \n для корректного парсинга ключа
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

    return Credentials.from_service_account_info(creds_dict, scopes=scopes)
