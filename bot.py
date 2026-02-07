# AradVIP Bot - نسخه نهایی کامل با اتصال مرزبان اتوماتیک
import os
import sqlite3
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from datetime import datetime

# ================== توکن ==================
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("توکن BOT_TOKEN در Environment Variables تعریف نشده است!")

# ================== اطلاعات مرزبان ==================
MARZBAN_USERNAME = os.environ.get("1804445169")  # یوزرنیم مرزبان
MARZBAN_PASSWORD = os.environ.get("1804445169")  # پسوورد مرزبان
MARZBAN_API_URL = "https://api.marzban.com"  # مثال آدرس API

# ================== دیتابیس ==================
DB_FILE = "aradvip.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    balance INTEGER DEFAULT 0,
                    role TEXT DEFAULT 'user',
                    join_date TEXT,
                    referrer INTEGER
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    plan TEXT,
                    price INTEGER,
                    date TEXT,
                    marzban_token TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
                    referrer INTEGER,
                    referee INTEGER
                )''')
    conn.commit()
    conn.close()

# ================== اتصال به مرزبان ==================
def create_marzban_token(plan_name: str):
    payload = {"username": MARZBAN_USERNAME, "password": MARZBAN_PASSWORD, "plan": plan_name}
    try:
        response = requests.post(f"{MARZBAN_API_URL}/create-token", json=payload, timeout=15)
        data = response.json()
        if response.status_code == 200 and data.get("token"):
            return data["token"]
        else:
            return None
    except Exception as e:
        print(f"Error creating Marzban token: {e}")
        return None

# ================== منوها ==================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 خرید اشتراک جدید", callback_data="buy")],
        [InlineKeyboardButton("👤 حساب کاربری", callback_data="account")],
        [InlineKeyboardButton("🎁 اشتراک تست", callback_data="test")],
        [InlineKeyboardButton("💬 پشتیبانی", callback_data="support")],
        [InlineKeyboardButton("🛠 پنل ادمین", callback_data="admin")]
    ])

def back_menu(target="back_main"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data=target)]])

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    username = update.effective_user.username
    args = context.args
    referrer_id = int(args[0]) if args else None

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users (id, username, join_date, referrer) VALUES (?, ?, ?, ?)",
                  (uid, username, datetime.now().strftime("%Y/%m/%d - %H:%M"), referrer_id))
        conn.commit()
        if referrer_id:
            c.execute("SELECT username FROM users WHERE id=?", (referrer_id,))
            ref_user = c.fetchone()
            if ref_user:
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=f"👤 {username} با لینک دعوت شما وارد ربات شد!"
                )

    conn.close()
    await update.message.reply_text("👋 به ربات AradVIP خوش آمدید", reply_markup=main_menu())

# ================== CALLBACK ==================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        if data == "back_main":
            await q.edit_message_text("🏠 منوی اصلی", reply_markup=main_menu())

        elif data == "account":
            c.execute("SELECT balance, role, join_date FROM users WHERE id=?", (uid,))
            user = c.fetchone()
            if user:
                balance, role, join_date = user
                c.execute("SELECT COUNT(*) FROM referrals WHERE referrer=?", (uid,))
                subs = c.fetchone()[0]
                await q.edit_message_text(
                    f"👤 شناسه کاربری: {uid}\n🔐 وضعیت: {role}\n💰 موجودی کیف پول: {balance:,} تومان\n👥 تعداد زیرمجموعه‌ها: {subs}\n📆 تاریخ عضویت: {join_date}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ افزایش موجودی", callback_data="topup")],
                        [InlineKeyboardButton("🔗 زیرمجموعه گیری", callback_data="referral")],
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
                    ])
                )

        elif data == "referral":
            link = f"https://t.me/YourBot?start={uid}"
            await q.edit_message_text(f"🔗 لینک اختصاصی شما برای دعوت دوستان:\n{link}", reply_markup=back_menu("account"))

        elif data.startswith("buy_"):
            plan = data.split("_")[1]
            price = int(data.split("_")[2])
            token = create_marzban_token(plan)
            if not token:
                await q.edit_message_text("❌ خطا در اتصال به مرزبان. لطفا بعدا امتحان کنید.", reply_markup=back_menu("back_main"))
                return

            c.execute("INSERT INTO orders (user_id, plan, price, date, marzban_token) VALUES (?, ?, ?, ?, ?)",
                      (uid, plan, price, datetime.now().strftime("%Y/%m/%d - %H:%M"), token))

            c.execute("SELECT referrer FROM users WHERE id=?", (uid,))
            ref = c.fetchone()[0]
            if ref:
                discount = int(price * 0.05)
                c.execute("UPDATE users SET balance = balance + ? WHERE id=?", (discount, ref))
                await context.bot.send_message(ref, f"💸 فلانی یک خرید انجام داد و شما {discount:,} تومان تخفیف دریافت کردید!")

            conn.commit()
            await q.edit_message_text(f"✅ خرید شما ثبت شد و توکن مرزبان: {token}", reply_markup=back_menu("back_main"))

    except Exception as e:
        await q.edit_message_text(f"❌ خطا: {e}", reply_markup=back_menu("back_main"))

    conn.commit()
    conn.close()

# ================== دریافت رسید پرداخت ==================
async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    amount = context.user_data.get('pending_topup')
    if not amount:
        await update.message.reply_text("❌ هیچ پرداختی در انتظار نیست.", reply_markup=main_menu())
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE id=?", (uid,))
    user = c.fetchone()
    if user:
        balance = user[0] + amount
        c.execute("UPDATE users SET balance=? WHERE id=?", (balance, uid))
    else:
        c.execute("INSERT INTO users (id, balance, join_date) VALUES (?, ?, ?)",
                  (uid, amount, datetime.now().strftime("%Y/%m/%d - %H:%M")))
    conn.commit()
    conn.close()
    context.user_data['pending_topup'] = None
    await update.message.reply_text(f"✅ موجودی شما به مبلغ {amount:,} تومان افزایش یافت", reply_markup=main_menu())

# ================== MAIN ==================
def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, receive_receipt))
    app.run_polling()

if __name__ == "__main__":
    main()
