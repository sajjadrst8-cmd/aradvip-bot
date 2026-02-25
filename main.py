import logging
from aiogram import executor
from loader import dp
import admin_handlers
import marzban_handlers
import buy_handlers
import handlers


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def on_startup(dispatcher):
    print("🚀 Bot is Online!")
    logger.info("ربات با موفقیت در ری‌ل‌وی اجرا شد.")

if __name__ == '__main__':
    # شروع به کار ربات
    # skip_updates=True باعث می‌شود پیام‌هایی که موقع خاموش بودن ربات ارسال شده، نادیده گرفته شوند
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
