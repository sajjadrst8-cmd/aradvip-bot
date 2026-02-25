# در فایل main.py
import logging
from aiogram import executor
from loader import dp

# اول هندلرهای اختصاصی
import buy_handlers
import admin_handlers
import marzban_handlers
# در آخر هندلرهای عمومی و استارت
import handlers 


async def on_startup(dispatcher):
    print("🚀 Bot is Online!")
    logger.info("ربات با موفقیت در ری‌ل‌وی اجرا شد.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
