import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ----------------------------
# تنظیمات و متغیرها
# ----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")  # توکن تلگرام از متغیر محیطی
WELCOME_TEXT = "سلام! به ربات خوش آمدید."

# ----------------------------
# لاگینگ
# ----------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------------------
# کیبورد اصلی
# ----------------------------
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("خرید", callback_data="buy")],
        [InlineKeyboardButton("پشتیبانی", callback_data="support")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ----------------------------
# هندلر استارت
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, reply_markup=main_menu_keyboard())

# ----------------------------
# تست اتصال به Marzban API
# ----------------------------
import requests

MARZBAN_URL = os.getenv("MARZBAN_URL", "https://v2inj.galexystore.ir/api/auth/login")
MARZBAN_USER = os.getenv("MARZBAN_USER")
MARZBAN_PASS = os.getenv("MARZBAN_PASS")

def login_to_marzban():
    try:
        r = requests.post(MARZBAN_URL, json={"username": MARZBAN_USER, "password": MARZBAN_PASS})
        r.raise_for_status()
        logger.info("ورود به Marzban موفق بود")
        return r.json()
    except requests.HTTPError as e:
        logger.error(f"خطا در ورود به Marzban: {e}")
        return None

# ----------------------------
# اجرای ربات
# ----------------------------
if __name__ == "__main__":
    login_to_marzban()  # تست اتصال به API قبل از استارت

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # وب‌هوک: آدرس باید با دامنه شما و مسیر HTTPS باشه
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # مثلا https://example.com/<bot_token>
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8443)),
        webhook_url=WEBHOOK_URL
    )