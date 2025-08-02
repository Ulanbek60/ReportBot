# Cafe Report Bot

Telegram-бот для кафе, который:
- собирает ежедневную выручку от владельца,
- уведомляет инвестора (7% от суммы),
- загружает фото в Google Drive,
- ведёт учёт в Google Sheets с автоформулами.

## Стек технологий
- Python 3.11
- Aiogram v3
- Google Sheets / Drive API
- Railway (деплой)

## Переменные окружения
Создайте `.env`:
```env
TELEGRAM_TOKEN=...
INVESTOR_ID=...
OWNER_ID=...
GSHEET_NAME=...
DRIVE_FOLDER_ID=...
