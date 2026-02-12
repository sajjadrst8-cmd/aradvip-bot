import logging, os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
# وارد کردن توابع از فایل‌های خودت
from database import get_user, users_col
import markups as nav

# --- تنظیمات ---
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 863961919 # آیدی عددی شما

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- هندلر دستور استارت ---
@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message):
    referrer = message.get_args()
    user = await get_user(message.from_user.id, referrer)
    
    # اطلاع‌رسانی به معرف (زیرمجموعه‌گیری)
    if referrer and str(referrer).isdigit() and int(referrer) != message.from_user.id:
        try:
            await bot.send_message(referrer, f"🔔 کاربر {message.from_user.id} با لینک دعوت شما وارد ربات شد.")
        except:
            pass

    await message.answer("لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=nav.main_menu())

# --- بخش مدیریت و تایید ادمین ---
@dp.callback_query_handler(lambda c: c.data.startswith("admin_"), state="*")
async def admin_verify(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    status = parts[1] # ok یا no
    uid = int(parts[2])
    amt = float(parts[3])

    if status == "ok":
        # اضافه کردن موجودی به کیف پول در دیتابیس مانگو
        await users_col.update_one({"user_id": uid}, {"$inc": {"wallet": amt}})
        
        # ارسال پیام موفقیت به کاربر
        try:
            await bot.send_message(uid, f"✅ رسید شما تأیید شد!\nمبلغ {amt:,} تومان به حساب شما اضافه شد.\nاکنون می‌توانید اشتراک خود را فعال کنید.")
        except:
            pass
            
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ توسط ادمین تایید و شارژ شد.")
    else:
        # اطلاع‌رسانی رد رسید به کاربر
        try:
            await bot.send_message(uid, "❌ رسید واریزی شما توسط مدیریت تأیید نشد.\nلطفاً تصویر واضح‌تری بفرستید یا با پشتیبانی در ارتباط باشید.")
        except:
            pass
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ رسید رد شد.")
    
    await callback.answer()

# --- وارد کردن تمام هندلرهای فایل handlers.py ---
# خیلی مهم: این خط باید حتماً بعد از تعریف dp باشد
import handlers

# --- اجرای ربات ---
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
