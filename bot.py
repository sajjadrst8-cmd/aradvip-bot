import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ---------- خواندن توکن ربات و اطلاعات Marzban از Railway ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
MARZBAN_URL = os.getenv("MARZBAN_URL")
MARZBAN_USERNAME = os.getenv("MARZBAN_USERNAME")
MARZBAN_PASSWORD = os.getenv("MARZBAN_PASSWORD")

# ---------- دیتابیس موقتی در RAM ----------
users_db = {}  # uid: {wallet, subscriptions, referrer, join_date, role}
referrals_db = {}  # inviter_uid: [invitee_uid]

# ---------- توابع Marzban ----------
def marzban_login():
    url = f"{MARZBAN_URL}/api/login"
    data = {"username": MARZBAN_USERNAME, "password": MARZBAN_PASSWORD}
    resp = requests.post(url, json=data)
    if resp.status_code == 200:
        return resp.json().get("token")
    else:
        raise Exception("⚠️ ورود به Marzban موفق نبود")

def create_subscription(token, username, plan):
    url = f"{MARZBAN_URL}/api/subscription/create"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"username": username, "plan": plan}
    resp = requests.post(url, json=data, headers=headers)
    return resp.json()  # {'username':..., 'password':...}

def check_subscription(token, username):
    url = f"{MARZBAN_URL}/api/subscription/{username}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    return resp.json()

# ---------- منو اصلی ----------
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💳 خرید اشتراک جدید", callback_data="buy_new")],
        [InlineKeyboardButton("🧪 دریافت اشتراک تست", callback_data="get_test")],
        [InlineKeyboardButton("👤 حساب کاربری", callback_data="account")],
        [
            InlineKeyboardButton("📞 پشتیبانی", callback_data="support"),
            InlineKeyboardButton("📚 آموزش اتصال", callback_data="tutorial")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ---------- هندلر استارت ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in users_db:
        users_db[uid] = {"wallet": 0, "subscriptions": [], "referrer": None, "join_date": "1403/12/23", "role": "user"}
    await update.message.reply_text("به ربات خوش آمدید!", reply_markup=main_menu_keyboard())

# ---------- هندلر دکمه‌ها ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    if query.data == "buy_new":
        keyboard = [
            [InlineKeyboardButton("V2Ray", callback_data="buy_v2ray")],
            [InlineKeyboardButton("Biubiu VPN", callback_data="buy_biubiu")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
        ]
        await query.edit_message_text("نوع اشتراک را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "get_test":
        keyboard = [
            [InlineKeyboardButton("تست V2Ray", callback_data="test_v2ray")],
            [InlineKeyboardButton("تست Biubiu VPN", callback_data="test_biubiu")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
        ]
        await query.edit_message_text("اشتراک تست خود را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "account":
        user = users_db.get(uid)
        text = f"👤 شناسه کاربری: {uid}\n🔐 وضعیت: {user['role']}\n💰 موجودی کیف پول: {user['wallet']} تومان\n"\
               f"👥 تعداد زیرمجموعه‌ها: {len(referrals_db.get(uid, []))}\n📆 تاریخ عضویت: {user['join_date']}"
        keyboard = [
            [InlineKeyboardButton("➕ افزایش موجودی", callback_data="add_wallet")],
            [InlineKeyboardButton("👥 زیرمجموعه گیری", callback_data="referral")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "support":
        text = "جهت ارتباط با ادمین به آیدی زیر پیام دهید:\n@AradVIP"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back")]]))

    elif query.data == "tutorial":
        text = "برای آموزش اتصال، به کانال زیر مراجعه کنید:"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("کانال آموزش‌ها", url="https://t.me/your_channel")],
                                                                              [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]]))

    elif query.data.startswith("buy_"):
        plan_type = query.data.split("_")[1]  # v2ray یا biubiu
        token = marzban_login()
        sub = create_subscription(token, f"user_{uid}", plan="1_month_" + plan_type)
        await query.edit_message_text(f"✅ اشتراک شما ساخته شد:\nیوزرنیم: {sub['username']}\nپسورد: {sub['password']}",
                                      reply_markup=main_menu_keyboard())

    elif query.data.startswith("test_"):
        plan_type = query.data.split("_")[1]
        await query.edit_message_text(f"✅ اشتراک تست {plan_type.upper()} ساخته شد",
                                      reply_markup=main_menu_keyboard())

    elif query.data == "back":
        await query.edit_message_text("بازگشت به منوی اصلی:", reply_markup=main_menu_keyboard())

# ---------- هندلر اصلی ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
