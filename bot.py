import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- تنظیمات اصلی ---
TOKEN = "8531397872:AAEi36WyX5DOW_GLk6yL44bHVjx0jw2pVn4" # توکن ربات را اینجا بگذار
ADMIN_ID = 863961919  # آیدی عددی خودت را اینجا بگذار
CARD_NUMBER = "6037-9999-8888-7777"
CARD_NAME = "سجاد رستگاران"
DB_NAME = "bot_data.db"

# --- تعرفه‌ها ---
V2RAY_SUBS = [
    {"name": "5 گیگ", "price": 60000}, {"name": "10 گیگ", "price": 100000},
    {"name": "20 گیگ", "price": 150000}, {"name": "30 گیگ", "price": 200000},
    {"name": "50 گیگ", "price": 300000}, {"name": "100 گیگ", "price": 400000}
]
BIU_S = [{"name": "1 ماهه", "price": 100000}, {"name": "2 ماهه", "price": 200000}]
BIU_M = [{"name": "1 ماهه نامحدود", "price": 300000}, {"name": "3 ماهه نامحدود", "price": 500000}]

# --- مدیریت دیتابیس ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS subs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan TEXT, link TEXT)')
    conn.commit()
    conn.close()

def get_bal(uid):
    conn = sqlite3.connect(DB_NAME); res = conn.execute('SELECT balance FROM users WHERE user_id=?', (uid,)).fetchone(); conn.close()
    return res[0] if res else 0

def update_bal(uid, amt):
    conn = sqlite3.connect(DB_NAME)
    conn.execute('INSERT OR IGNORE INTO users VALUES (?, 0)', (uid,))
    conn.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amt, uid))
    conn.commit(); conn.close()

init_db()

# --- دستور شارژ دستی توسط ادمین ---
# نحوه استفاده: /charge 12345678 50000
async def charge_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        update_bal(target_id, amount)
        await update.message.reply_text(f"✅ مبلغ {amount:,} به حساب {target_id} اضافه شد.")
        await context.bot.send_message(target_id, f"💰 حساب شما توسط مدیریت مبلغ {amount:,} تومان شارژ شد.")
    except:
        await update.message.reply_text("❌ روش اشتباه! مثال:\n/charge 12345678 50000")

# --- مدیریت خرید و منوها ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("💳 خرید اشتراک جدید", callback_data="buy_new")],
          [InlineKeyboardButton("📋 اشتراک‌های من", callback_data="my_subs")],
          [InlineKeyboardButton("👤 حساب و شارژ", callback_data="account")]]
    text = "به ربات VIP خوش آمدید. گزینه مورد نظر را انتخاب کنید:"
    if update.message: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else: await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

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

async def select_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, stype, price, name = update.callback_query.data.split("|")
    context.user_data['order'] = {"type": stype, "price": int(price), "name": name}
    kb = [[InlineKeyboardButton("💰 پرداخت از کیف پول", callback_data="pay_wallet")],
          [InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card")],
          [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")]]
    await update.callback_query.message.edit_text(f"سرویس: {name}\nمبلغ: {int(price):,} تومان\nروش پرداخت؟", reply_markup=InlineKeyboardMarkup(kb))

async def pay_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id
    order = context.user_data.get('order')
    if get_bal(uid) >= order['price']:
        update_bal(uid, -order['price'])
        # در اینجا می‌توانید کد مرزبان را صدا بزنید (بعداً)
        await update.callback_query.message.edit_text(f"✅ پرداخت از کیف پول انجام شد.\nاشتراک {order['name']} برای شما فعال شد.",
                                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 اشتراک‌های من", callback_data="my_subs")]]))
    else:
        await update.callback_query.answer("❌ موجودی کافی نیست!", show_alert=True)

async def pay_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['wait_receipt'] = True
    kb = [[InlineKeyboardButton("🔙 انصراف و بازگشت", callback_data="start")]]
    await update.callback_query.message.edit_text(f"💳 شماره کارت: `{CARD_NUMBER}`\n👤 بنام: {CARD_NAME}\n\nلطفاً عکس رسید را بفرستید:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('wait_receipt') and update.message.photo:
        uid = update.message.from_user.id
        order = context.user_data.get('order')
        kb = [[InlineKeyboardButton("✅ تایید", callback_data=f"ok_{uid}"), InlineKeyboardButton("❌ رد", callback_data=f"no_{uid}")]]
        await context.bot.send_photo(ADMIN_ID, update.message.photo[-1].file_id, caption=f"رسید از {uid}\nبرای: {order['name']}\nمبلغ: {order['price']:,}", reply_markup=InlineKeyboardMarkup(kb))
        await update.message.reply_text("✅ تصویر ارسال شد و در انتظار تأیید ادمین است. کمتر از ۱۰ دقیقه دیگر تأیید می‌شود.")
        context.user_data['wait_receipt'] = False

async def admin_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    uid = int(data.split("_")[1])
    if data.startswith("ok_"):
        await context.bot.send_message(uid, "✅ رسید شما تایید شد و اشتراک فعال گشت.\nاز بخش 'اشتراک‌های من' مشاهده کنید.")
        await update.callback_query.edit_message_caption("🟢 رسید تایید شد.")
    else:
        await context.bot.send_message(uid, "❌ رسید شما توسط ادمین رد شد.")
        await update.callback_query.edit_message_caption("🔴 رسید رد شد.")

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bal = get_bal(update.callback_query.from_user.id)
    kb = [[InlineKeyboardButton("➕ شارژ (کارت به کارت)", callback_data="pay_card")], [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    await update.callback_query.message.edit_text(f"👤 حساب کاربری\n🆔 آیدی شما: {update.callback_query.from_user.id}\n💰 موجودی: {bal:,} تومان", reply_markup=InlineKeyboardMarkup(kb))

# --- اجرای ربات ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("charge", charge_user))
app.add_handler(CallbackQueryHandler(start, pattern="^start$"))
app.add_handler(CallbackQueryHandler(buy_new, pattern="^buy_new$"))
app.add_handler(CallbackQueryHandler(list_v2ray, pattern="^list_v2ray$"))
app.add_handler(CallbackQueryHandler(list_biubiu, pattern="^list_biubiu$"))
app.add_handler(CallbackQueryHandler(biu_single, pattern="^biu_single$"))
app.add_handler(CallbackQueryHandler(select_pay, pattern="^pay\|"))
app.add_handler(CallbackQueryHandler(pay_wallet, pattern="^pay_wallet$"))
app.add_handler(CallbackQueryHandler(pay_card, pattern="^pay_card$"))
app.add_handler(CallbackQueryHandler(account, pattern="^account$"))
app.add_handler(CallbackQueryHandler(admin_verify, pattern="^(ok|no)_"))
app.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
app.run_polling()
