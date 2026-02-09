import sqlite3
import qrcode
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- تنظیمات اصلی ---
TOKEN = "8531397872:AAEi36WyX5DOW_GLk6yL44bHVjx0jw2pVn4"
ADMIN_ID = 863961919 
CARD_NUMBER = "6037-9999-8888-7777"
CARD_NAME = "سجاد رستگاران"
DB_NAME = "bot_data.db"

# --- لیست کامل تعرفه‌ها ---
V2RAY_SUBS = [
    {"name": "5 گیگ", "price": 60000}, {"name": "10 گیگ", "price": 100000},
    {"name": "20 گیگ", "price": 150000}, {"name": "30 گیگ", "price": 200000},
    {"name": "50 گیگ", "price": 300000}, {"name": "100 گیگ", "price": 400000}
]

BIU_S = [
    {"name": "Biubiu 1 ماهه (تک)", "price": 100000},
    {"name": "Biubiu 2 ماهه (تک)", "price": 200000},
    {"name": "Biubiu 3 ماهه (تک)", "price": 300000}
]

BIU_M = [
    {"name": "Biubiu 1 ماهه (نامحدود)", "price": 300000},
    {"name": "Biubiu 3 ماهه (نامحدود)", "price": 500000},
    {"name": "Biubiu 6 ماهه (نامحدود)", "price": 1100000},
    {"name": "Biubiu 12 ماهه (نامحدود)", "price": 1200000}
]

# --- دیتابیس ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS subs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan TEXT, link TEXT, username TEXT)')
    conn.commit()
    conn.close()

init_db()

def get_bal(uid):
    conn = sqlite3.connect(DB_NAME); res = conn.execute('SELECT balance FROM users WHERE user_id=?', (uid,)).fetchone(); conn.close()
    return res[0] if res else 0

def update_bal(uid, amt):
    conn = sqlite3.connect(DB_NAME)
    conn.execute('INSERT OR IGNORE INTO users VALUES (?, 0)', (uid,))
    conn.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amt, uid))
    conn.commit(); conn.close()

# --- منوی اصلی ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("💳 خرید اشتراک جدید", callback_data="buy_new")],
          [InlineKeyboardButton("📋 اشتراک‌های من", callback_data="my_subs")],
          [InlineKeyboardButton("👤 حساب و شارژ", callback_data="account")]]
    text = "به ربات VIP خوش آمدید. گزینه مورد نظر را انتخاب کنید:"
    if update.message: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else: await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

# --- بخش خرید و پرداخت ---
async def buy_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("📡 v2ray", callback_data="list_v2ray")],
          [InlineKeyboardButton("🚀 biubiu VPN", callback_data="list_biubiu")],
          [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    await update.callback_query.message.edit_text("سرویس مورد نظر:", reply_markup=InlineKeyboardMarkup(kb))

async def list_v2ray(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(f"{s['name']} - {s['price']:,}", callback_data=f"pay|v2|{s['price']}|{s['name']}")] for s in V2RAY_SUBS]
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")])
    await update.callback_query.message.edit_text("تعرفه‌های v2ray:", reply_markup=InlineKeyboardMarkup(kb))

async def list_biubiu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("👤 1 کاربره", callback_data="biu_single")],
          [InlineKeyboardButton("👥 2 کاربره", callback_data="biu_multi")],
          [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")]]
    await update.callback_query.message.edit_text("تعداد کاربر Biubiu:", reply_markup=InlineKeyboardMarkup(kb))

async def biu_single(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(f"{s['name']} - {s['price']:,}", callback_data=f"pay|biu|{s['price']}|{s['name']}")] for s in BIU_S]
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="list_biubiu")])
    await update.callback_query.message.edit_text("تعرفه‌های تک‌کاربره:", reply_markup=InlineKeyboardMarkup(kb))

async def biu_multi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(f"{s['name']} - {s['price']:,}", callback_data=f"pay|biu|{s['price']}|{s['name']}")] for s in BIU_M]
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="list_biubiu")])
    await update.callback_query.message.edit_text("تعرفه‌های چندکاربره:", reply_markup=InlineKeyboardMarkup(kb))

async def select_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, stype, price, name = update.callback_query.data.split("|")
    context.user_data['order'] = {"type": stype, "price": int(price), "name": name}
    kb = [[InlineKeyboardButton("💰 پرداخت از کیف پول", callback_data="pay_wallet")],
          [InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card")],
          [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")]]
    await update.callback_query.message.edit_text(f"سرویس: {name}\nمبلغ: {int(price):,} تومان\nروش پرداخت؟", reply_markup=InlineKeyboardMarkup(kb))

# --- نمایش اشتراک (قالب درخواستی) ---
async def show_sub_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sub_id = update.callback_query.data.split("_")[2]
    conn = sqlite3.connect(DB_NAME)
    sub = conn.execute('SELECT plan, link, username FROM subs WHERE id=?', (sub_id,)).fetchone()
    conn.close()
    
    plan, link, username = sub
    text = f"""📊 جزئیات اشتراک:
وضعیت: 🟢 فعال
👤 نام کاربری: {username if username else 'نامشخص'}
📥 مصرف‌شده: 0 GiB
📊 باقیمانده: نامحدود GiB
📆 زمان باقی‌مانده: ∞ بدون محدودیت

🔗 لینک اشتراک:
`{link}`

📘 آموزش وارد کردن لینک اشتراک:
[لینک آموزش را اینجا بگذارید]
"""
    kb = [[InlineKeyboardButton("🖼 دریافت QR Code", callback_data=f"qr_{sub_id}")],
          [InlineKeyboardButton("🔙 بازگشت", callback_data="my_subs")]]
    await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def my_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id
    conn = sqlite3.connect(DB_NAME)
    subs = conn.execute('SELECT id, plan FROM subs WHERE user_id=?', (uid,)).fetchall()
    conn.close()
    
    if not subs:
        await update.callback_query.message.edit_text("شما اشتراک فعالی ندارید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]))
        return

    kb = [[InlineKeyboardButton(f"📦 {s[1]}", callback_data=f"show_sub_{s[0]}")] for s in subs]
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="start")])
    await update.callback_query.message.edit_text("لیست اشتراک‌های شما برای مشاهده جزئیات کلیک کنید:", reply_markup=InlineKeyboardMarkup(kb))

# --- هندلرهای دیگر (کارت به کارت و تایید ادمین) ---
async def pay_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['wait_receipt'] = True
    await update.callback_query.message.edit_text(f"💳 شماره کارت: `{CARD_NUMBER}`\n👤 بنام: {CARD_NAME}\n\nلطفاً رسید را ارسال کنید:", parse_mode="Markdown")

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('wait_receipt') and update.message.photo:
        uid = update.message.from_user.id
        order = context.user_data.get('order')
        kb = [[InlineKeyboardButton("✅ تایید", callback_data=f"ok_{uid}"), InlineKeyboardButton("❌ رد", callback_data=f"no_{uid}")]]
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=f"رسید از {uid}\nبرای: {order['name']}", reply_markup=InlineKeyboardMarkup(kb))
        await update.message.reply_text("✅ تصویر رسید ارسال شد و در انتظار تأیید ادمین هست و در کمتر از ده دقیقه تأیید می‌شود.")
        context.user_data['wait_receipt'] = False

async def admin_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    uid = int(data.split("_")[1])
    if data.startswith("ok_"):
        # اینجا باید یوزرنیم و لینک واقعی مرزبان ساخته شود
        link = "vless://auto-generated-link"
        uname = f"User_{uid}"
        conn = sqlite3.connect(DB_NAME)
        conn.execute('INSERT INTO subs (user_id, plan, link, username) VALUES (?, ?, ?, ?)', (uid, "اشتراک تایید شده", link, uname))
        conn.commit(); conn.close()
        await context.bot.send_message(uid, "✅ رسید شما تأیید شد و اشتراک شما ساخته شد، برای مشاهده‌ی مشخصات اشتراک گزینه زیر را فشار دهید.", 
                                       reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 اشتراک‌های من", callback_data="my_subs")]]))
        await update.callback_query.edit_message_caption("🟢 تایید شد.")
    else:
        await context.bot.send_message(uid, "❌ رسید شما رد شد.")

# --- اجرای ربات ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(start, pattern="^start$"))
app.add_handler(CallbackQueryHandler(buy_new, pattern="^buy_new$"))
app.add_handler(CallbackQueryHandler(list_v2ray, pattern="^list_v2ray$"))
app.add_handler(CallbackQueryHandler(list_biubiu, pattern="^list_biubiu$"))
app.add_handler(CallbackQueryHandler(biu_single, pattern="^biu_single$"))
app.add_handler(CallbackQueryHandler(biu_multi, pattern="^biu_multi$"))
app.add_handler(CallbackQueryHandler(select_pay, pattern="^pay\|"))
app.add_handler(CallbackQueryHandler(my_subs, pattern="^my_subs$"))
app.add_handler(CallbackQueryHandler(show_sub_detail, pattern="^show_sub_"))
app.add_handler(CallbackQueryHandler(admin_verify, pattern="^(ok|no)_"))
app.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
app.run_polling()
