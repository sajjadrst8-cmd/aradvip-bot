import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- تنظیمات ---
ADMIN_ID = 12345678  # آیدی عددی خودت را اینجا بزن
CARD_NUMBER = "6037-9999-8888-7777"
CARD_NAME = "سجاد رستگاران"
DB_NAME = "bot_data.db"

# --- دیتای اشتراک‌ها ---
V2RAY_SUBS = [
    {"name": "5 گیگ نامحدود", "price": 60000},
    {"name": "10 گیگ نامحدود", "price": 100000},
    {"name": "20 گیگ نامحدود", "price": 150000},
    {"name": "30 گیگ نامحدود", "price": 200000},
    {"name": "50 گیگ نامحدود", "price": 300000},
]

BIUVIU_SINGLE = [{"name": "1 ماهه", "price": 100000}, {"name": "2 ماهه", "price": 200000}]
BIUVIU_MULTI = [{"name": "1 ماهه نامحدود", "price": 300000}, {"name": "3 ماهه نامحدود", "price": 500000}]

# --- مدیریت دیتابیس ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS subs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan TEXT, link TEXT)')
    conn.commit()
    conn.close()

def get_bal(uid):
    conn = sqlite3.connect(DB_NAME)
    res = conn.execute('SELECT balance FROM users WHERE user_id=?', (uid,)).fetchone()
    conn.close()
    return res[0] if res else 0

def add_bal(uid, amt):
    conn = sqlite3.connect(DB_NAME)
    conn.execute('INSERT OR IGNORE INTO users VALUES (?, 0)', (uid,))
    conn.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amt, uid))
    conn.commit()
    conn.close()

init_db()

# --- هندلرهای ربات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("💳 خرید اشتراک جدید", callback_data="buy_new")],
        [InlineKeyboardButton("📋 اشتراک‌های من", callback_data="my_subs")],
        [InlineKeyboardButton("👤 حساب و شارژ", callback_data="account")],
        [InlineKeyboardButton("📞 پشتیبانی", url="https://t.me/AradVIP")]
    ]
    text = "خوش آمدید! یکی از گزینه‌ها را انتخاب کنید:"
    if update.message: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else: await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def buy_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("📡 v2ray", callback_data="list_v2ray")],
        [InlineKeyboardButton("🚀 biubiu VPN", callback_data="list_biubiu")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
    ]
    await update.callback_query.message.edit_text("نوع سرویس:", reply_markup=InlineKeyboardMarkup(kb))

async def list_v2ray(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(f"{s['name']} - {s['price']:,}", callback_data=f"pay|v2ray|{s['price']}|{s['name']}")] for s in V2RAY_SUBS]
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")])
    await update.callback_query.message.edit_text("تعرفه‌های v2ray:", reply_markup=InlineKeyboardMarkup(kb))

async def list_biubiu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("👤 1 کاربره", callback_data="biu_s"), InlineKeyboardButton("👥 2 کاربره", callback_data="biu_m")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")]
    ]
    await update.callback_query.message.edit_text("انتخاب نوع اشتراک biubiu:", reply_markup=InlineKeyboardMarkup(kb))

async def biu_s(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(f"{s['name']} - {s['price']:,}", callback_data=f"pay|biubiu|{s['price']}|{s['name']}")] for s in BIUVIU_SINGLE]
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="list_biubiu")])
    await update.callback_query.message.edit_text("تعرفه‌های تک‌کاربره:", reply_markup=InlineKeyboardMarkup(kb))

async def select_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, stype, price, name = update.callback_query.data.split("|")
    context.user_data['order'] = {"type": stype, "price": int(price), "name": name}
    kb = [
        [InlineKeyboardButton("💰 پرداخت از کیف پول", callback_data="pay_wallet")],
        [InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")]
    ]
    await update.callback_query.message.edit_text(f"خرید {name}\nمبلغ: {int(price):,} تومان\nروش پرداخت؟", reply_markup=InlineKeyboardMarkup(kb))

async def pay_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['wait_receipt'] = True
    await update.callback_query.message.edit_text(f"مبلغ را به کارت زیر واریز و رسید بفرستید:\n\n`{CARD_NUMBER}`\n{CARD_NAME}", parse_mode="Markdown")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('wait_receipt'):
        uid = update.message.from_user.id
        order = context.user_data.get('order')
        kb = [[InlineKeyboardButton("✅ تایید", callback_data=f"ok_{uid}"), InlineKeyboardButton("❌ رد", callback_data=f"no_{uid}")]]
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=f"رسید از {uid}\nبرای: {order['name']}", reply_markup=InlineKeyboardMarkup(kb))
        await update.message.reply_text("رسید ارسال شد. پس از تایید ادمین (کمتر از ۱۰ دقیقه) اطلاع می‌دهیم.")
        context.user_data['wait_receipt'] = False

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    uid = int(data.split("_")[1])
    if data.startswith("ok_"):
        # در اینجا می‌توانید تابع Marzban را صدا بزنید
        link = "vless://auto-generated-link-here" 
        conn = sqlite3.connect(DB_NAME)
        conn.execute('INSERT INTO subs (user_id, plan, link) VALUES (?, ?, ?)', (uid, "اکانت خریداری شده", link))
        conn.commit()
        conn.close()
        await context.bot.send_message(uid, "✅ رسید تایید شد! اشتراک ساخته شد. از بخش 'اشتراک‌های من' دریافت کنید.")
        await update.callback_query.edit_message_caption("تایید شد.")
    else:
        await context.bot.send_message(uid, "❌ رسید شما توسط ادمین رد شد.")
        await update.callback_query.edit_message_caption("رد شد.")

async def my_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id
    conn = sqlite3.connect(DB_NAME)
    subs = conn.execute('SELECT plan, link FROM subs WHERE user_id=?', (uid,)).fetchall()
    conn.close()
    text = "اشتراک‌های شما:\n\n" + "\n".join([f"📦 {s[0]}\n`{s[1]}`" for s in subs]) if subs else "اشتراکی ندارید."
    await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]), parse_mode="Markdown")

# --- استارت ربات ---
app = ApplicationBuilder().token("8531397872:AAEi36WyX5DOW_GLk6yL44bHVjx0jw2pVn4").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(start, pattern="^start$"))
app.add_handler(CallbackQueryHandler(buy_new, pattern="^buy_new$"))
app.add_handler(CallbackQueryHandler(list_v2ray, pattern="^list_v2ray$"))
app.add_handler(CallbackQueryHandler(list_biubiu, pattern="^list_biubiu$"))
app.add_handler(CallbackQueryHandler(biu_s, pattern="^biu_s$"))
app.add_handler(CallbackQueryHandler(select_pay, pattern="^pay\|"))
app.add_handler(CallbackQueryHandler(pay_card, pattern="^pay_card$"))
app.add_handler(CallbackQueryHandler(my_subs, pattern="^my_subs$"))
app.add_handler(CallbackQueryHandler(admin_action, pattern="^(ok|no)_"))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.run_polling()
