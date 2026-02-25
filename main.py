import logging
from aiogram import executor
from loader import dp

# --- اضافه کردن هندلرهای دیگر ---
import admin_handlers
import marzban_handlers
import buy_handlers
import handlers

# ۱. اول لاگر را تعریف کن (این بخش خیلی مهم است)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__) # این خط باید قبل از تابع on_startup باشد

# ۲. حالا تابع on_startup می‌تواند از logger استفاده کند
async def on_startup(dispatcher):
    print("🚀 Bot is Online!")
    logger.info("ربات با موفقیت در ری‌ل‌وی اجرا شد.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
