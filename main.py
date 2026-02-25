import logging
from aiogram import executor
from loader import dp

# اولویت‌بندی ایمپورت هندلرها (بسیار مهم)
import buy_handlers
import admin_handlers
import marzban_handlers
import handlers # همیشه آخرین مورد باشد

# تنظیمات لاگر برای نمایش اتفاقات در Railway
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def on_startup(dispatcher):
    # این خط را طبق لاگ Railway اصلاح کردم
    logger.info("🚀 ربات با موفقیت آنلاین شد و در حال شنود پیام‌هاست.")

if __name__ == '__main__':
    # استفاده از skip_updates برای نادیده گرفتن پیام‌های زمان قطعی
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
