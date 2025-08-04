from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

def main():
    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets"
    ]
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secrets.json",
        scopes=scopes
    )

    # Показываем ссылку вручную
    auth_url, _ = flow.authorization_url(prompt='consent')
    print("🔗 Перейди по ссылке и авторизуйся:")
    print(auth_url)

    # Вставляем код вручную
    code = input("📥 Вставь код авторизации сюда: ")

    # Получаем токен
    flow.fetch_token(code=code)

    creds = flow.credentials
    with open("credentials.json", "wb") as token:
        pickle.dump(creds, token)

    print("✅ Авторизация прошла успешно.")

if __name__ == "__main__":
    main()
