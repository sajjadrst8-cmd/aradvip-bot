import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- تنظیمات از محیط (Environment Variables) ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MARZBAN_USERNAME = os.getenv("MARZBAN_USERNAME")
MARZBAN_PASSWORD = os.getenv("MARZBAN_PASSWORD")
MARZBAN_API_BASE = "https://v2inj.galexystore.ir/api"

# اطلاعات کارت بانکی
CARD_NUMBER = os.getenv("CARD_NUMBER", "6037-xxxx-xxxx-xxxx")
CARD_NAME = os.getenv("CARD_NAME", "نام صاحب حساب")

# ---- توابع کمکی مرزبان ----
def get_marzban_token():
    try:
        resp = requests.post(f"{MARZBAN_API_BASE}/auth/login",
                             data={"username": MARZBAN_USERNAME, "password": MARZBAN_PASSWORD}) # مرزبان معمولا فرم دیتا میگیرد
        resp.raise_for_status()
        return resp.json()["access_token"]
    except Exception as e:
        print("خطا در گرفتن توکن مرزبان:", e)
        return None

def get_services(token):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(f"{MARZBAN_API_BASE}/service", headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print("خطا در گرفتن سرویس‌ها:", e)
        return []

# ---- توابع ساخت منو (برای جلوگیری از تکرار کد) ----
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💳 خرید اشتراک جدید", callback_data="buy_new")],
        [InlineKeyboardButton("🧪 دریافت اشتراک تست", callback_data="buy_test")],
        [InlineKeyboardButton("👤 حساب کاربری", callback_data="account")],
        [
            InlineKeyboardButton("📞 پشتیبانی", url="https://t.me/AradVIP"),
            InlineKeyboardButton("📚 آموزش اتصال", url="https://t.me/joinchat/...")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ---- هندلرهای اصلی ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "سلام! به ربات مدیریت اشتراک خوش آمدید.\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard())
    else:
        await update.callback_query.message.edit_text(text, reply_markup=main_menu_keyboard())

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = (
        f"👤 شناسه کاربری: `{query.from_user.id}`\n"
        "🔐 وضعیت: کاربر عادی\n"
        "💰 موجودی کیف پول: 0 تومان\n"
        "--------------------------\n"
        "جهت خرید ابتدا موجودی خود را افزایش دهید."
    )
    keyboard = [
        [InlineKeyboardButton("➕ افزایش موجودی (کارت به کارت)", callback_data="wallet_add")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def wallet_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = (
        "💳 **روش پرداخت کارت به کارت**\n\n"
        f"شماره کارت: `{5057851560122225}`\n"
        f"به نام: **{سجاد رستگاران}**\n\n"
        "⚠️ پس از واریز، حتماً تصویر رسید را برای پشتیبانی (@AradVIP) ارسال کنید تا موجودی شما شارژ شود."
    )
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="account")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "start":
        await start(update, context)
    elif data == "account":
        await account(update, context)
    elif data == "wallet_add":
        await wallet_add(update, context)
    elif data == "buy_new":
        keyboard = [
            [InlineKeyboardButton("V2Ray", callback_data="service_v2ray")],
            [InlineKeyboardButton("Biubiu VPN", callback_data="service_biubiu")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
        ]
        await query.message.edit_text("لطفا نوع اشتراک را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    # ... سایر شرط‌ها (buy_test و غیره) را می‌توانید اینجا نگه دارید یا اضافه کنید
    elif data.startswith("service_"):
        await query.message.edit_text("در حال دریافت لیست قیمت‌ها از سرور...")
        # منطق دریافت سرویس‌ها از مرزبان که قبلاً نوشتید...

# ---- اجرای ربات ----
if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN:
        print("خطا: توکن ربات تنظیم نشده است!")
    else:
        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button))
        
        print("Bot is running...")
        app.run_polling(drop_pending_updates=True)
