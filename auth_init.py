from google_auth_oauthlib.flow import InstalledAppFlow
import os

SCOPES = ["https://www.googleapis.com/auth/drive"]

def main():
    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
    creds = flow.run_local_server(port=0)
    with open("token.json", "w") as token_file:
        token_file.write(creds.to_json())
    print("✅ Авторизация успешна. Файл token.json сохранён.")

if __name__ == "__main__":
    main()
