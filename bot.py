import sqlite3
import requests
import re
import qrcode
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- تنظیمات ---
MARZBAN_URL = "https://v2inj.galexystore.ir"
MARZBAN_ADMIN_USER = "1804445169"
MARZBAN_ADMIN_PASS = "1804445169"
TOKEN = "8222529473:AAGO_jtCpQNx6qG8Kmd3BgCcweyxcQWFjSM"
ADMIN_ID = 863961919 
CARD_NUMBER = "6037-9999-8888-7777"
CARD_NAME = "سجاد رستگاران"
DB_NAME = "bot_data.db"

V2RAY_SUBS = [
    {"name": "5 گیگ", "price": 60000},
    {"name": "10 گیگ", "price": 100000},
    {"name": "20 گیگ", "price": 150000}
]

# --- توابع کمکی ---
def get_marzban_token():
    try:
        url = f"{MARZBAN_URL}/api/admin/token"
        data = {'username': MARZBAN_ADMIN_USER, 'password': MARZBAN_ADMIN_PASS}
        response = requests.post(url, data=data, timeout=10)
        return response.json().get('access_token')
    except: return None

def create_marzban_user(user_id, plan_name):
    token = get_marzban_token()
    if not token: return None, None
    gb = int(re.findall(r'\d+', plan_name)[0]) if re.findall(r'\d+', plan_name) else 10
    bytes_limit = gb * 1024 * 1024 * 1024
    
    headers = {'Authorization': f'Bearer {token}'}
    username = f"tg_{user_id}_{int(requests.utils.time.time())}"
    payload = {"username": username, "proxies": {"vless": {}, "vmess": {}}, "data_limit": bytes_limit}
    
    try:
        res = requests.post(f"{MARZBAN_URL}/api/user", json=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json().get('subscription_url'), username
    except: pass
    return None, None

# --- مدیریت دیتابیس ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS subs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan TEXT, link TEXT, username TEXT)')
    conn.commit(); conn.close()

init_db()

# --- هندلرهای اصلی ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = sqlite3.connect(DB_NAME)
    if not conn.execute('SELECT user_id FROM users WHERE user_id=?', (uid,)).fetchone():
        conn.execute('INSERT INTO users (user_id) VALUES (?)', (uid,))
        conn.commit()
    conn.close()

    kb = [[InlineKeyboardButton("💳 خرید اشتراک جدید", callback_data="buy_new")],
          [InlineKeyboardButton("📋 اشتراک‌های من", callback_data="my_subs")],
          [InlineKeyboardButton("👤 حساب و شارژ", callback_data="account")]]
    text = "🚀 به ربات فروش فیلترشکن خوش آمدید!\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    
    if update.message: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else: await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def account_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id
    conn = sqlite3.connect(DB_NAME)
    bal = conn.execute('SELECT balance FROM users WHERE user_id=?', (uid,)).fetchone()[0]
    conn.close()
    
    text = f"👤 مشخصات حساب شما:\n\n🆔 آیدی عددی: `{uid}`\n💰 موجودی: {bal:,} تومان"
    kb = [[InlineKeyboardButton("➕ شارژ کیف پول", callback_data="pay_card")],
          [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def buy_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(f"{p['name']} - {p['price']:,} تومان", callback_data=f"sel|{p['price']}|{p['name']}")] for p in V2RAY_SUBS]
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="start")])
    await update.callback_query.message.edit_text("لطفاً پکیج مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

async def select_pay_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, price, name = update.callback_query.data.split("|")
    context.user_data['order'] = {"price": int(price), "name": name}
    kb = [[InlineKeyboardButton("💰 پرداخت از کیف پول", callback_data="pay_wallet")],
          [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")]]
    await update.callback_query.message.edit_text(f"سرویس: {name}\nقیمت: {int(price):,} تومان\nروش پرداخت را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

async def pay_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id
    order = context.user_data.get('order')
    if not order: return
    
    conn = sqlite3.connect(DB_NAME)
    bal = conn.execute('SELECT balance FROM users WHERE user_id=?', (uid,)).fetchone()[0]
    
    if bal >= order['price']:
        sub_url, uname = create_marzban_user(uid, order['name'])
        if sub_url:
            conn.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (order['price'], uid))
            conn.execute('INSERT INTO subs (user_id, plan, link, username) VALUES (?, ?, ?, ?)', (uid, order['name'], sub_url, uname))
            conn.commit()
            await update.callback_query.message.edit_text("✅ پرداخت موفق! اشتراک شما ساخته شد.\nاز بخش 'اشتراک‌های من' لینک را دریافت کنید.")
        else:
            await update.callback_query.answer("❌ خطا در اتصال به پنل مرزبان!", show_alert=True)
    else:
        await update.callback_query.answer("❌ موجودی کیف پول کافی نیست!", show_alert=True)
    conn.close()

async def pay_card_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"💳 جهت شارژ حساب، مبلغ مورد نظر را به کارت زیر واریز کنید:\n\n`{CARD_NUMBER}`\n👤 به نام: {CARD_NAME}\n\n📸 سپس عکس رسید را در همین‌جا ارسال کنید."
    await update.callback_query.message.edit_text(text, parse_mode="Markdown")

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo = update.message.photo[-1].file_id
        uid = update.message.from_user.id
        kb = [[InlineKeyboardButton("✅ تایید (۵۰ هزارتومان)", callback_data=f"adm_50000_{uid}"),
               InlineKeyboardButton("✅ تایید (۱۰۰ هزارتومان)", callback_data=f"adm_100000_{uid}")],
              [InlineKeyboardButton("❌ رد رسید", callback_data=f"adm_reject_{uid}")]]
        
        await context.bot.send_photo(ADMIN_ID, photo, caption=f"رسید جدید از: {uid}", reply_markup=InlineKeyboardMarkup(kb))
        await update.message.reply_text("⏳ رسید شما برای ادمین ارسال شد. پس از تایید حساب شما شارژ می‌شود.")

async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data.split("_")
    action = data[1]
    target_uid = int(data[2])
    
    conn = sqlite3.connect(DB_NAME)
    if action == "reject":
        await context.bot.send_message(target_uid, "❌ رسید شما توسط ادمین رد شد.")
        await update.callback_query.edit_message_caption("🔴 رد شد.")
    else:
        amount = int(action)
        conn.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, target_uid))
        conn.commit()
        await context.bot.send_message(target_uid, f"✅ حساب شما مبلغ {amount:,} تومان شارژ شد.")
        await update.callback_query.edit_message_caption(f"🟢 تایید شد ({amount:,} تومان)")
    conn.close()

async def my_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id
    conn = sqlite3.connect(DB_NAME)
    subs = conn.execute('SELECT id, plan FROM subs WHERE user_id=?', (uid,)).fetchall()
    conn.close()
    if not subs:
        await update.callback_query.message.edit_text("شما هیچ اشتراک فعالی ندارید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]))
        return
    kb = [[InlineKeyboardButton(f"📦 {s[1]}", callback_data=f"show_{s[0]}")] for s in subs]
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="start")])
    await update.callback_query.message.edit_text("لیست اشتراک‌های شما:", reply_markup=InlineKeyboardMarkup(kb))

async def show_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid = update.callback_query.data.split("_")[1]
    conn = sqlite3.connect(DB_NAME)
    sub = conn.execute('SELECT plan, link, username FROM subs WHERE id=?', (sid,)).fetchone()
    conn.close()
    text = f"📋 اشتراک: {sub[0]}\n👤 یوزرنیم: `{sub[2]}`\n\n🔗 لینک اتصال:\n`{sub[1]}`"
    await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="my_subs")]]), parse_mode="Markdown")

# --- استارت ربات ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^start$"))
    app.add_handler(CallbackQueryHandler(buy_new, pattern="^buy_new$"))
    app.add_handler(CallbackQueryHandler(account_info, pattern="^account$"))
    app.add_handler(CallbackQueryHandler(select_pay_method, pattern="^sel\|"))
    app.add_handler(CallbackQueryHandler(pay_wallet, pattern="^pay_wallet$"))
    app.add_handler(CallbackQueryHandler(pay_card_info, pattern="^pay_card$"))
    app.add_handler(CallbackQueryHandler(my_subs, pattern="^my_subs$"))
    app.add_handler(CallbackQueryHandler(show_sub, pattern="^show_"))
    app.add_handler(CallbackQueryHandler(admin_decision, pattern="^adm_"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt))

    print("✅ ربات آنلاین شد!")
    app.run_polling()
