from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
import asyncio
import logging
import config_example as config
from services.google_sheets import append_to_sheet, is_report_already_submitted
from services.notifier import notify_owner
from services.photo_upload import upload_photo_to_drive
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
import html
import json

# Восстановление google_credentials.json из переменной среды
if os.getenv("GOOGLE_CREDENTIALS_JSON"):
    with open("google_credentials.json", "w") as f:
        json.dump(json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON")), f)


class ReportStates(StatesGroup):
    idle = State()
    waiting_for_income = State()
    waiting_for_photo = State()
    waiting_for_date = State()
    waiting_for_comment = State()
    waiting_for_investor_message = State()

router = Router()

@router.message(CommandStart())
async def start_command(msg: Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="▶️ Старт")]], resize_keyboard=True
    )
    await msg.answer("👋 Добро пожаловать! Нажми кнопку ниже, чтобы начать.", reply_markup=kb)
    await state.set_state(ReportStates.idle)

@router.message(F.text == "▶️ Старт")
async def start_pressed(msg: Message, state: FSMContext):
    kb_buttons = [[KeyboardButton(text="📄 Отправить отчет")]]
    if str(msg.from_user.id) == os.getenv("INVESTOR_ID"):
        kb_buttons.append([KeyboardButton(text="📨 Отправить сообщение владельцу")])
    kb = ReplyKeyboardMarkup(keyboard=kb_buttons, resize_keyboard=True)
    await msg.answer("✅ Отлично! Выбери действие:", reply_markup=kb)

@router.message(lambda msg: msg.text and "Отправить отчет" in msg.text)
async def report_entry(msg: Message, state: FSMContext):
    await msg.answer("💰 Введите сумму дохода за сегодня:")
    await state.set_state(ReportStates.waiting_for_income)

@router.message(lambda msg: msg.text and "Отправить сообщение владельцу" in msg.text)
async def investor_message_start(msg: Message, state: FSMContext):
    if str(msg.from_user.id) != os.getenv("INVESTOR_ID"):
        await msg.answer("❌ У вас нет прав для этой команды.")
        return
    await msg.answer("✏️ Напишите сообщение, которое будет отправлено владельцу кафе:")
    await state.set_state(ReportStates.waiting_for_investor_message)

@router.message(ReportStates.waiting_for_investor_message)
async def receive_investor_message(msg: Message, state: FSMContext):
    owner_id = int(os.getenv("OWNER_ID"))
    await msg.bot.send_message(owner_id, f"📨 <b>Сообщение от инвестора:</b>\n{html.escape(msg.text)}", parse_mode="HTML")
    await msg.answer("✅ Сообщение отправлено владельцу кафе")
    await state.set_state(ReportStates.idle)

@router.message(ReportStates.waiting_for_income)
async def get_income(msg: Message, state: FSMContext):
    try:
        income = float(msg.text)
        await state.update_data(income=income)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📷❌Без фото", callback_data="skip_photo")]
        ])
        await msg.answer("📷 Теперь отправьте фото отчета", reply_markup=kb)
        await state.set_state(ReportStates.waiting_for_photo)
    except ValueError:
        await msg.answer("❌ Введите цифру дохода")

@router.message(ReportStates.waiting_for_photo)
async def get_photo(msg: Message, state: FSMContext, bot: Bot):
    if not msg.photo:
        return await msg.answer("❌ Это не фото. Пожалуйста, отправьте фото или нажмите кнопку \"Отправить без фото\".")

    photo = msg.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_path = f"data/report_{msg.chat.id}_{photo.file_id}.jpg"
    await bot.download_file(file.file_path, photo_path)
    await state.update_data(photo_path=photo_path)

    await ask_for_date(msg, state)

@router.callback_query(F.data == "skip_photo")
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    await state.update_data(photo_path=None)
    await callback.answer()
    await ask_for_date(callback.message, state)

async def ask_for_date(msg: Message, state: FSMContext):
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📅 Сегодня ({today.strftime('%d.%m.%Y')})", callback_data="date_today")],
        [InlineKeyboardButton(text=f"📆 Вчера ({yesterday.strftime('%d.%m.%Y')})", callback_data="date_yesterday")]
    ])
    await msg.answer("📆 Укажите, за какой день отчёт:", reply_markup=kb)
    await state.set_state(ReportStates.waiting_for_date)

@router.callback_query(F.data.in_(["date_today", "date_yesterday"]))
async def handle_date(callback: CallbackQuery, state: FSMContext):
    choice = callback.data
    report_date = datetime.now().date() if choice == "date_today" else datetime.now().date() - timedelta(days=1)
    report_date_str = report_date.strftime("%d.%m.%Y")

    if is_report_already_submitted(report_date_str):
        await callback.message.answer("⚠️ Отчёт за эту дату уже был отправлен. Повторная отправка невозможна.")
        await state.set_state(ReportStates.idle)
        return

    await state.update_data(report_date=report_date_str)
    await callback.message.answer("✍️ Напишите комментарий или нажмите кнопку ниже:", reply_markup=
        InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✉️ Отправить без комментария", callback_data="skip_comment")]
        ])
    )
    await callback.answer()
    await state.set_state(ReportStates.waiting_for_comment)

@router.callback_query(F.data == "skip_comment")
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    await save_report(callback.message, state, comment="—")
    await callback.message.answer("✅ Отчёт отправлен инвестору")
    await state.set_state(ReportStates.idle)
    await callback.answer()

@router.message(ReportStates.waiting_for_comment)
async def get_comment(msg: Message, state: FSMContext):
    await save_report(msg, state, comment=msg.text)
    await msg.answer("✅ Отчёт отправлен инвестору")
    await state.set_state(ReportStates.idle)

async def save_report(msg, state, comment: str):
    data = await state.get_data()
    income = data.get("income")
    photo_path = data.get("photo_path")
    report_date = data.get("report_date")
    percent = round(income * 0.07, 2)
    drive_url = "—"

    if photo_path:
        try:
            drive_url = upload_photo_to_drive(photo_path, report_date)
        except Exception as e:
            error_msg = html.escape(str(e))
            await msg.answer(f"❌ Ошибка при загрузке фото:\n<pre>{error_msg}</pre>", parse_mode="HTML")

    append_to_sheet(report_date, income, percent, drive_url, comment)

    await msg.bot.send_message(
        int(os.getenv("INVESTOR_ID")),
        f"📥 <b>Отчёт от владельца кафе:</b>\n"
        f"📅 <b>Дата:</b> {report_date}\n"
        f"💰 <b>Доход:</b> {income} сом\n"
        f"📊 <b>7% инвестору:</b> {percent} сом\n"
        f"🖼️ <b>Фото:</b> {drive_url}\n"
        f"💬 <b>Комментарий:</b> {comment or '—'}",
        parse_mode="HTML"
    )

@router.message()
async def unknown_input(msg: Message, state: FSMContext):
    current_state = await state.get_state()
    allowed_states = [
        ReportStates.waiting_for_income.state,
        ReportStates.waiting_for_photo.state,
        ReportStates.waiting_for_comment.state,
        ReportStates.waiting_for_date.state,
        ReportStates.waiting_for_investor_message.state
    ]
    allowed_texts = ["📄 Отправить отчет", "▶️ Старт", "📨 Отправить сообщение владельцу"]

    if msg.text in allowed_texts or current_state in allowed_states:
        return

    await msg.answer("❌ Пожалуйста, пользуйтесь кнопками. Текст здесь не нужен.")

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage(), fsm_strategy=FSMStrategy.CHAT)
    dp.include_router(router)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(notify_owner, 'cron', hour=21, minute=0, args=[bot])
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
