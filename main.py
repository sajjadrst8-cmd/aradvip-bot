import logging, os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from database import get_user, users_col
import markups as nav

# --- تنظیمات ---
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 863961919
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# --- هندلرهای پایه ---
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    # ... کدهای قبلی استارت ...
    await message.answer("لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=nav.main_menu())

# --- بخش تایید ادمین (دقیقا اینجا اضافه کن) ---
@dp.callback_query_handler(lambda c: c.data.startswith("admin_"))
async def admin_verify(callback: types.CallbackQuery):
    # تجزیه اطلاعات از دکمه: admin_ok_USERID_AMOUNT
    parts = callback.data.split("_")
    status = parts[1] # ok یا no
    uid = int(parts[2])
    amt = float(parts[3])

    if status == "ok":
        # اضافه کردن پول به کیف پول کاربر در مانگو
        await users_col.update_one({"user_id": uid}, {"$inc": {"wallet": amt}})
        
        # اطلاع‌رسانی به کاربر
        await bot.send_message(uid, f"✅ رسید شما توسط مدیریت تأیید شد!\nمبلغ {amt:,} تومان به کیف پول شما اضافه شد.")
        
        # تغییر متن دکمه برای ادمین
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ تأیید و شارژ شد.")
    else:
        await bot.send_message(uid, "❌ رسید واریزی شما توسط مدیریت تأیید نشد.\nدر صورت بروز مشکل با پشتیبانی در ارتباط باشید.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ رد شد.")
    
    await callback.answer()

# --- وارد کردن هندلرهای دیگر ---
import handlers 

# --- اجرای ربات ---
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
