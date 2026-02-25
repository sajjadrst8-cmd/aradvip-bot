import logging
from aiogram import executor
from loader import dp

# تنظیمات لاگینگ را ابتدا انجام بده
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# حالا هندلرها را ایمپورت کن (ترتیب مهم است)
import admin_handlers
import marzban_handlers
import buy_handlers
import handlers  # این همیشه آخری باشد چون هندلرهای عمومی در آن است

async def on_startup(dispatcher):
    print("🚀 Bot is Online!")
    logger.info("ربات با موفقیت در ری‌ل‌وی اجرا شد.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
