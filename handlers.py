from aiogram import types
from loader import dp, bot
from database import get_user
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from states import BuyState
import markups as nav
    
@dp.message_handler(commands=['start'], state="*")
async def start_handler(message: types.Message, state: FSMContext):
    await state.finish() # ریست کردن وضعیت کاربر
    
    user_id = message.from_user.id
    first_name = message.from_user.first_name # نام کاربر
    
    # متنی که خواسته بودی
    welcome_text = (
        f"سلام {first_name} عزیز\n"
        f"به سیستم هوشمند فروش آراد وی ای پی خوش آمدید\n"
        f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    # ارسال پیام همراه با پاس دادن user_id به کیبورد
    await message.answer(welcome_text, reply_markup=nav.main_menu(user_id))

# --- هندلر بازگشت به منوی اصلی (از همه جا) ---
@dp.callback_query_handler(lambda c: c.data == "main_menu", state="*")
async def back_to_main(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    
    user_id = call.from_user.id
    first_name = call.from_user.first_name
    
    text = (
        f"سلام {first_name}\n"
        f"به منوی اصلی بازگشتید. لطفاً انتخاب کنید:"
    )
    
    await call.message.edit_text(text, reply_markup=nav.main_menu(user_id))

# سایر هندلرهای عمومی (مثل دکمه پشتیبانی)
@dp.callback_query_handler(lambda c: c.data == "support", state="*")
async def support_handler(call: types.CallbackQuery):
    await call.message.answer("💎 برای ارتباط با پشتیبانی به آیدی @Arad_Support پیام دهید.")
    await call.answer()
