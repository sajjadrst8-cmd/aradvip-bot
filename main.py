import logging
from aiogram import executor
# دقت کن: فقط ایمپورت لودر و هندلرز
from loader import dp
import handlers 

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    # ربات از اینجا روشن می‌شه و میره سراغ کدهای handlers
    executor.start_polling(dp, skip_updates=True)
