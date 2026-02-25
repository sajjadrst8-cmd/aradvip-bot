import os
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

storage = MemoryStorage() # ابتدا در یک متغیر تعریف کن
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=storage) # متغیر را اینجا پاس بده
