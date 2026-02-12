import logging, os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from database import get_user, users_col
import markups as nav

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 863961919

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    referrer = message.get_args()
    user = await get_user(message.from_user.id, referrer)
    
    # اگر زیرمجموعه کسی شده باشد
    if referrer and int(referrer) != message.from_user.id:
        try:
            await bot.send_message(referrer, f"🔔 کاربر {message.from_user.id} با لینک شما وارد شد.")
        except: pass

    await message.answer("لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=nav.main_menu())

@dp.callback_query_handler(lambda c: c.data == "account")
async def account(callback: types.CallbackQuery):
    u = await get_user(callback.from_user.id)
    text = (f"👤 شناسه کاربری: {u['user_id']}\n"
            f"🔐 وضعیت: 👤 کاربر عادی\n"
            f"💰 موجودی کیف پول: {u['wallet']:,} تومان\n"
            f"👥 تعداد زیرمجموعه‌ها: 0\n\n"
            f"📆 تاریخ عضویت: {u['join_date']}")
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("➕ افزایش موجودی", callback_data="charge_wallet"),
           types.InlineKeyboardButton("👥 زیرمجموعه‌گیری", callback_data="ref_link"),
           types.InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu"))
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def back_main(callback: types.CallbackQuery):
    await callback.message.edit_text("لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=nav.main_menu())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
