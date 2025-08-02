import config

async def notify_owner(bot):
    await bot.send_message(config.OWNER_ID, "⏰ Напоминание: вы ещё не отправили отчёт за сегодня!")
