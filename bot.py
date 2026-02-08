import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- خواندن توکن از env ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MARZBAN_USERNAME = os.getenv("MARZBAN_USERNAME")
MARZBAN_PASSWORD = os.getenv("MARZBAN_PASSWORD")

MARZBAN_API_BASE = "https://v2inj.galexystore.ir/api"

# ---- اتصال به مرزبان ----
def get_marzban_token():
    try:
        resp = requests.post(f"{MARZBAN_API_BASE}/auth/login",
                             json={"username": MARZBAN_USERNAME, "password": MARZBAN_PASSWORD})
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
        return resp.json()  # فرض: JSON شامل id، name، price
    except Exception as e:
        print("خطا در گرفتن سرویس‌ها:", e)
        return []

def create_user_service(token, service_id, username):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"username": username, "service_id": service_id, "expire": 30}
    try:
        resp = requests.post(f"{MARZBAN_API_BASE}/users", json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print("خطا در ساخت اکانت:", e)
        return None

# ---- منوها ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💳 خرید اشتراک جدید", callback_data="buy_new")],
        [InlineKeyboardButton("🧪 دریافت اشتراک تست", callback_data="buy_test")],
        [InlineKeyboardButton("👤 حساب کاربری", callback_data="account")],
        [
            InlineKeyboardButton("📞 پشتیبانی", url="https://t.me/AradVIP"),
            InlineKeyboardButton("📚 آموزش اتصال", url="https://t.me/joinchat/...")  # لینک کانال آموزش
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("سلام! من ربات مدیریت اشتراک تو هستم:", reply_markup=reply_markup)

# ---- خرید اشتراک ----
async def buy_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("V2Ray", callback_data="service_v2ray")],
        [InlineKeyboardButton("Biubiu VPN", callback_data="service_biubiu")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text("لطفا نوع اشتراک را انتخاب کنید:", reply_markup=reply_markup)

async def buy_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("V2Ray تست", callback_data="test_v2ray")],
        [InlineKeyboardButton("Biubiu VPN تست", callback_data="test_biubiu")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text("انتخاب اشتراک تست:", reply_markup=reply_markup)

# ---- حساب کاربری ----
async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👤 شناسه کاربری: 863961919\n"
        "🔐 وضعیت: کاربر عادی\n"
        "💰 موجودی کیف پول: 146,900 تومان\n"
        "👥 تعداد زیرمجموعه‌ها: 1\n"
        "📆 تاریخ عضویت: 1403/12/23 - 09:59"
    )
    keyboard = [
        [InlineKeyboardButton("➕ افزایش موجودی", callback_data="wallet_add")],
        [InlineKeyboardButton("🔗 زیرمجموعه گیری", callback_data="referral")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text(text, reply_markup=reply_markup)

# ---- کال‌بک‌ها ----
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "start":
        await start(update, context)
    elif data == "buy_new":
        await buy_new(update, context)
    elif data == "buy_test":
        await buy_test(update, context)
    elif data == "account":
        await account(update, context)
    elif data.startswith("service_") or data.startswith("test_"):
        token = get_marzban_token()
        if not token:
            await query.message.edit_text("خطا در اتصال به مرزبان!")
            return
        service_type = data.split("_")[1]  # v2ray, biubiu
        services = get_services(token)
        keyboard = []
        for s in services:
            if (service_type.lower() in s["name"].lower()):
                keyboard.append([InlineKeyboardButton(f"{s['name']} - {s['price']} تومان", callback_data=f"buy_{s['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("اشتراک‌های موجود:", reply_markup=reply_markup)
    elif data.startswith("buy_"):
        service_id = int(data.split("_")[1])
        token = get_marzban_token()
        username = str(query.from_user.id)
        result = create_user_service(token, service_id, username)
        if result:
            await query.message.edit_text(f"اکانت شما ساخته شد!\nنام کاربری: {username}\nسرویس: {service_id}")
        else:
            await query.message.edit_text("خطا در ساخت اکانت!")

# ---- اجرای ربات ----
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()
