from aiogram import types
from loader import dp, bot
from database import save_receipt, is_duplicate_receipt
from config import ADMIN_ID

@dp.message_handler(content_types=['photo'], state=BuyState.waiting_for_receipt)
async def handle_payment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # منطق بررسی رسید تکراری و ارسال به ادمین
    # ساخت دکمه‌های تایید/رد برای ادمین
    await message.answer("✅ رسید شما برای ادمین ارسال شد.")
    await state.finish()
