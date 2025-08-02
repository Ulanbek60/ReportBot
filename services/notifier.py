import config
from aiogram import Bot

async def notify_owner(bot: Bot):
    await bot.send_message(
        config.OWNER_ID,
        "⏰ Напоминание: вы ещё не отправили отчёт за сегодня!"
    )
