import os
import sqlite3
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

# ================== توکن از Environment Variable ==================
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("توکن BOT_TOKEN در Environment Variables تعریف نشده است!")

# ================== دیتابیس ==================
DB_FILE = "aradvip.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # جدول کاربران
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    balance INTEGER DEFAULT 0,
                    role TEXT DEFAULT 'user',
                    join_date TEXT,
                    referrer INTEGER
                )''')
    # جدول سفارشات
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    plan TEXT,
                    price INTEGER,
                    date TEXT
                )''')
    # جدول ادمین‌ها
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY
                )''')
    # جدول زیرمجموعه‌ها
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
                    referrer INTEGER,
                    referee INTEGER
                )''')
    conn.commit()
    conn.close()

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
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (uid,))
    user = c.fetchone()
    if not user:
        c.execute(
            "INSERT INTO users (id, username, join_date) VALUES (?, ?, ?)",
            (uid, username, datetime.now().strftime("%Y/%m/%d - %H:%M"))
        )
        conn.commit()
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
        # ---------- بازگشت ----------
        if data == "back_main":
            await q.edit_message_text("🏠 منوی اصلی", reply_markup=main_menu())

        # ---------- حساب کاربری ----------
        elif data == "account":
            c.execute("SELECT balance, role, join_date FROM users WHERE id=?", (uid,))
            user = c.fetchone()
            if user:
                balance, role, join_date = user
                # تعداد زیرمجموعه
                c.execute("SELECT COUNT(*) FROM referrals WHERE referrer=?", (uid,))
                subs = c.fetchone()[0]
                await q.edit_message_text(
                    f"""👤 شناسه کاربری: {uid}
🔐 وضعیت: {role}
💰 موجودی کیف پول: {balance:,} تومان
👥 تعداد زیرمجموعه‌ها: {subs}
📆 تاریخ عضویت: {join_date}""",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ افزایش موجودی", callback_data="topup")],
                        [InlineKeyboardButton("🔗 زیرمجموعه گیری", callback_data="referral")],
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
                    ])
                )

        # ---------- افزایش موجودی ----------
        elif data == "topup":
            await q.edit_message_text(
                "💳 مبلغ افزایش موجودی را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💵 100,000 تومان", callback_data="topup_100")],
                    [InlineKeyboardButton("💵 200,000 تومان", callback_data="topup_200")],
                    [InlineKeyboardButton("💵 500,000 تومان", callback_data="topup_500")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="account")]
                ])
            )

        elif data.startswith("topup_"):
            amount = int(data.split("_")[1])*1000
            await q.edit_message_text(
                f"💳 پرداخت کارت به کارت\nمبلغ: {amount:,} تومان\n\n📌 پس از پرداخت، رسید را ارسال کنید.",
                reply_markup=back_menu("account")
            )
            context.user_data['pending_topup'] = amount

        # ---------- خرید ----------
        elif data == "buy":
            await q.edit_message_text(
                "📦 نوع اشتراک را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚀 V2Ray", callback_data="buy_v2ray")],
                    [InlineKeyboardButton("📱 Biubiu VPN", callback_data="buy_biubiu")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
                ])
            )

        # ---------- سیستم زیرمجموعه گیری ----------
        elif data == "referral":
            link = f"https://t.me/YourBot?start={uid}"
            await q.edit_message_text(
                f"🔗 لینک اختصاصی شما:\n{link}\nهر کسی با این لینک وارد شد، زیرمجموعه شما محسوب می‌شود.",
                reply_markup=back_menu("account")
            )

        # ---------- پنل ادمین ----------
        elif data == "admin":
            c.execute("SELECT * FROM admins WHERE user_id=?", (uid,))
            if not c.fetchone():
                await q.edit_message_text("❌ دسترسی ادمین ندارید", reply_markup=back_menu("back_main"))
            else:
                await q.edit_message_text(
                    "🛠 پنل ادمین:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 گزارش مالی", callback_data="admin_report")],
                        [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")],
                        [InlineKeyboardButton("➕ اضافه کردن ادمین", callback_data="admin_add")],
                        [InlineKeyboardButton("➖ حذف ادمین", callback_data="admin_remove")],
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
                    ])
                )

        # ---------- سایر callback ها می توانند اضافه شوند ----------

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
        c.execute(
            "INSERT INTO users (id, balance, join_date) VALUES (?, ?, ?)",
            (uid, amount, datetime.now().strftime("%Y/%m/%d - %H:%M"))
        )
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
    app.add_handler(MessageHandler(filters.Document(True) | filters.PHOTO, receive_receipt))
    app.run_polling()

if __name__ == "__main__":
    main()