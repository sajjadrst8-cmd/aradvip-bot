import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- تنظیمات ---
ADMIN_ID = 863961919  # آیدی عددی خودت را بگذار
CARD_NUMBER = "6037-9999-8888-7777"
CARD_NAME = "سجاد رستگاران"
DB_NAME = "bot_data.db"

# --- لیست کامل تعرفه‌ها ---
V2RAY_SUBS = [
    {"name": "5 گیگ نامحدود", "price": 60000},
    {"name": "10 گیگ نامحدود", "price": 100000},
    {"name": "20 گیگ نامحدود", "price": 150000},
    {"name": "30 گیگ نامحدود", "price": 200000},
    {"name": "50 گیگ نامحدود", "price": 300000},
    {"name": "100 گیگ نامحدود", "price": 400000},
    {"name": "200 گیگ نامحدود", "price": 500000},
]

BIU_S = [
    {"name": "1 ماهه", "price": 100000},
    {"name": "2 ماهه", "price": 200000},
    {"name": "3 ماهه", "price": 300000},
]

BIU_M = [
    {"name": "1 ماهه نامحدود", "price": 300000},
    {"name": "3 ماهه نامحدود", "price": 500000},
    {"name": "6 ماهه نامحدود", "price": 1100000},
    {"name": "12 ماهه نامحدود", "price": 1200000},
]

# --- دیتابیس ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS subs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan TEXT, link TEXT)')
    conn.commit()
    conn.close()

def get_bal(uid):
    conn = sqlite3.connect(DB_NAME)
    res = conn.execute('SELECT balance FROM users WHERE user_id=?', (uid,)).fetchone()
    conn.close()
    return res[0] if res else 0

def update_bal(uid, amt):
    conn = sqlite3.connect(DB_NAME)
    conn.execute('INSERT OR IGNORE INTO users VALUES (?, 0)', (uid,))
    conn.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amt, uid))
    conn.commit()
    conn.close()

init_db()

# --- هندلرهای منو ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("💳 خرید اشتراک جدید", callback_data="buy_new")],
        [InlineKeyboardButton("📋 اشتراک‌های من", callback_data="my_subs")],
        [InlineKeyboardButton("👤 حساب و شارژ", callback_data="account")],
        [InlineKeyboardButton("📞 پشتیبانی", url="https://t.me/AradVIP")]
    ]
    text = "به ربات خوش آمدید:"
    if update.message: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else: await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def buy_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("📡 v2ray", callback_data="list_v2ray")],
        [InlineKeyboardButton("🚀 biubiu VPN", callback_data="list_biubiu")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
    ]
    await update.callback_query.message.edit_text("انتخاب نوع سرویس:", reply_markup=InlineKeyboardMarkup(kb))

async def list_v2ray(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(f"{s['name']} - {s['price']:,}", callback_data=f"pay|v2|{s['price']}|{s['name']}")] for s in V2RAY_SUBS]
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")])
    await update.callback_query.message.edit_text("تعرفه‌های v2ray:", reply_markup=InlineKeyboardMarkup(kb))

async def list_biubiu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("👤 1 کاربره", callback_data="biu_single")],
          [InlineKeyboardButton("👥 2 کاربره", callback_data="biu_multi")],
          [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")]]
    await update.callback_query.message.edit_text("تعداد کاربر biubiu را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

async def biu_single(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(f"{s['name']} - {s['price']:,}", callback_data=f"pay|biu|{s['price']}|{s['name']}")] for s in BIU_S]
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="list_biubiu")])
    await update.callback_query.message.edit_text("تعرفه‌های 1 کاربره biubiu:", reply_markup=InlineKeyboardMarkup(kb))

async def biu_multi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(f"{s['name']} - {s['price']:,}", callback_data=f"pay|biu|{s['price']}|{s['name']}")] for s in BIU_M]
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="list_biubiu")])
    await update.callback_query.message.edit_text("تعرفه‌های 2 کاربره biubiu:", reply_markup=InlineKeyboardMarkup(kb))

async def select_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, stype, price, name = update.callback_query.data.split("|")
    context.user_data['order'] = {"type": stype, "price": int(price), "name": name}
    kb = [[InlineKeyboardButton("💰 پرداخت از کیف پول", callback_data="pay_wallet")],
          [InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card")],
          [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")]]
    await update.callback_query.message.edit_text(f"سرویس: {name}\nقیمت: {int(price):,}\nروش پرداخت را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

async def pay_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id
    order = context.user_data.get('order')
    bal = get_bal(uid)
    if bal >= order['price']:
        update_bal(uid, -order['price'])
        # در اینجا می‌توانید کد ساخت اتوماتیک v2ray را هم بگذارید
        text = "✅ پرداخت با موفقیت انجام شد."
        kb = [[InlineKeyboardButton("📋 اشتراک‌های من", callback_data="my_subs")]]
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.callback_query.answer("❌ موجودی کافی نیست! حساب خود را شارژ کنید.", show_alert=True)

async def pay_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['wait_receipt'] = True
    kb = [[InlineKeyboardButton("🔙 انصراف و بازگشت", callback_data="start")]]
    await update.callback_query.message.edit_text(f"💳 شماره کارت: `{CARD_NUMBER}`\n👤 بنام: {CARD_NAME}\n\nلطفاً رسید را ارسال کنید:", 
                                                  reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id
    bal = get_bal(uid)
    kb = [[InlineKeyboardButton("➕ شارژ کیف پول", callback_data="pay_card")], [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    await update.callback_query.message.edit_text(f"💰 موجودی شما: {bal:,} تومان", reply_markup=InlineKeyboardMarkup(kb))

async def my_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id
    conn = sqlite3.connect(DB_NAME)
    subs = conn.execute('SELECT plan, link FROM subs WHERE user_id=?', (uid,)).fetchall()
    conn.close()
    text = "📋 اشتراک‌های شما:\n\n" + "\n\n".join([f"📦 {s[0]}\n`{s[1]}`" for s in subs]) if subs else "شما هنوز اشتراکی ندارید."
    await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]), parse_mode="Markdown")

# --- استارت ---
app = ApplicationBuilder().token("8531397872:AAEi36WyX5DOW_GLk6yL44bHVjx0jw2pVn4").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(start, pattern="^start$"))
app.add_handler(CallbackQueryHandler(buy_new, pattern="^buy_new$"))
app.add_handler(CallbackQueryHandler(list_v2ray, pattern="^list_v2ray$"))
app.add_handler(CallbackQueryHandler(list_biubiu, pattern="^list_biubiu$"))
app.add_handler(CallbackQueryHandler(biu_single, pattern="^biu_single$"))
app.add_handler(CallbackQueryHandler(biu_multi, pattern="^biu_multi$"))
app.add_handler(CallbackQueryHandler(select_pay, pattern="^pay\|"))
app.add_handler(CallbackQueryHandler(pay_card, pattern="^pay_card$"))
app.add_handler(CallbackQueryHandler(pay_wallet, pattern="^pay_wallet$"))
app.add_handler(CallbackQueryHandler(account, pattern="^account$"))
app.add_handler(CallbackQueryHandler(my_subs, pattern="^my_subs$"))
app.add_handler(MessageHandler(filters.PHOTO, lambda u, c: None)) # اینجا باید هندلر رسید را کامل کنید
app.run_polling()
