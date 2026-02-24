from aiogram import types
from loader import dp, bot
from database import get_user
from aiogram.dispatcher import FSMContext
import markups as nav

@dp.message_handler(commands=['start'], state="*")
async def start_handler(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    # منطق چک کردن ثبت‌نام کاربر در دیتابیس
    await message.answer(f"سلام خوش آمدید!", reply_markup=nav.main_menu())

@dp.callback_query_handler(lambda c: c.data == "main_menu", state="*")
async def back_to_main(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.edit_text("منوی اصلی:", reply_markup=nav.main_menu())
