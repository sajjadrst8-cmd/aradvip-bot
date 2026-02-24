import logging
from aiogram import executor
from loader import dp

# --- وارد کردن هندلرها به ترتیب اولویت ---
# ترتیب مهم است: ابتدا بخش‌های تخصصی و در آخر بخش‌های عمومی
import admin_handlers    # مدیریت تایید/رد و آمار
import marzban_handlers # توابع مربوط به API مرزبان
import buy_handlers      # بخش جدید خرید V2ray و BiuBiu (که جدا کردیم)
import handlers          # دستورات عمومی مثل /start و منوها

# تنظیمات لاگ برای مشاهده خطاها در Railway
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
