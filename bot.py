import sqlite3
import requests
import re
import qrcode
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- تنظیمات مرزبان ---
MARZBAN_URL = "https://v2inj.galexystore.ir"
MARZBAN_ADMIN_USER = "1804445169"
MARZBAN_ADMIN_PASS = "1804445169"

# --- تنظیمات ربات ---
TOKEN = "8222529473:AAGO_jtCpQNx6qG8Kmd3BgCcweyxcQWFjSM"
ADMIN_ID = 863961919 
CARD_NUMBER = "6037-9999-8888-7777"
CARD_NAME = "سجاد رستگاران"
DB_NAME = "bot_data.db"

# --- لیست تعرفه‌ها ---
V2RAY_SUBS = [
    {"name": "5 گیگ", "price": 60000}, {"name": "10 گیگ", "price": 100000},
    {"name": "20 گیگ", "price": 150000}, {"name": "50 گیگ", "price": 300000}
]

# --- توابع مرزبان ---
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
    digits = re.findall(r'\d+', plan_name)
    gb_limit = int(digits[0]) if digits else 10
    bytes_limit = gb_limit * 1024 * 1024 * 1024
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    username = f"tg_{user_id}_{int(requests.utils.time.time())}" # یوزرنیم یکتا
    
    payload = {"username": username, "proxies": {"vless": {}, "vmess": {}}, "data_limit": bytes_limit, "expire": 0}
    try:
        url = f"{MARZBAN_URL}/api/user"
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get('subscription_url'), username
    except: return None, None

async def get_sub_info(username):
    token = get_marzban_token()
    if not token: return None
    headers = {'Authorization': f'Bearer {token}'}
    try:
        url = f"{MARZBAN_URL}/api/user/{username}"
        res = requests.get(url, headers=headers, timeout=10)
        return res.json() if res.status_code == 200 else None
    except: return None

# --- دیتابیس ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS subs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan TEXT, link TEXT, username TEXT)')
    conn.commit(); conn.close()

init_db()

# --- هندلرهای تلگرام ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("💳 خرید اشتراک جدید", callback_data="buy_new")],
          [InlineKeyboardButton("📋 اشتراک‌های من", callback_data="my_subs")],
          [InlineKeyboardButton("👤 حساب و شارژ", callback_data="account")]]
    text = "به ربات خوش آمدید. گزینه مورد نظر را انتخاب کنید:"
    if update.message: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else: await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def buy_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(f"{s['name']} - {s['price']:,} تومان", callback_data=f"pay|v2|{s['price']}|{s['name']}")] for s in V2RAY_SUBS]
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="start")])
    await update.callback_query.message.edit_text("انتخاب حجم اشتراک:", reply_markup=InlineKeyboardMarkup(kb))

async def select_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, _, price, name = update.callback_query.data.split("|")
    context.user_data['order'] = {"price": int(price), "name": name}
    kb = [[InlineKeyboardButton("💰 پرداخت از کیف پول", callback_data="pay_wallet")],
          [InlineKeyboardButton("💳 کارت به کارت (تایید ادمین)", callback_data="pay_card")],
          [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")]]
    await update.callback_query.message.edit_text(f"سرویس: {name}\nقیمت: {int(price):,} تومان\nروش پرداخت را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

async def pay_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id
    order = context.user_data.get('order')
    conn = sqlite3.connect(DB_NAME)
    user = conn.execute('SELECT balance FROM users WHERE user_id=?', (uid,)).fetchone()
    bal = user[0] if user else 0
    
    if bal >= order['price']:
        sub_url, uname = create_marzban_user(uid, order['name'])
        if sub_url:
            conn.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (order['price'], uid))
            conn.execute('INSERT INTO subs (user_id, plan, link, username) VALUES (?, ?, ?, ?)', (uid, order['name'], sub_url, uname))
            conn.commit()
            await update.callback_query.message.edit_text("✅ پرداخت موفق! اشتراک ساخته شد. به منوی 'اشتراک‌های من' بروید.")
        else:
            await update.callback_query.answer("❌ خطا در پنل مرزبان!", show_alert=True)
    else:
        await update.callback_query.answer("❌ موجودی کافی نیست!", show_alert=True)
    conn.close()

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
    await update.callback_query.message.edit_text("لیست اشتراک‌های شما:", reply_markup=InlineKeyboardMarkup(kb))

async def show_sub_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sub_id = update.callback_query.data.split("_")[2]
    conn = sqlite3.connect(DB_NAME); sub = conn.execute('SELECT plan, link, username FROM subs WHERE id=?', (sub_id,)).fetchone(); conn.close()
    
    m_data = await get_sub_info(sub[2])
    status = "🟢 فعال" if m_data and m_data['status'] == 'active' else "🔴 غیرفعال"
    used = round(m_data['used_traffic']/(1024**3), 2) if m_data else 0
    total = round(m_data['data_limit']/(1024**3), 2) if m_data and m_data['data_limit'] else "نامحدود"

    text = f"📊 جزئیات اشتراک:\nوضعیت: {status}\n👤 یوزرنیم: `{sub[2]}`\n📥 مصرف: {used} GiB\n📊 کل: {total} GiB\n📆 زمان: ∞ نامحدود\n\n🔗 لینک:\n`{sub[1]}`"
    kb = [[InlineKeyboardButton("🖼 دریافت QR Code", callback_data=f"genqr_{sub_id}")],
          [InlineKeyboardButton("🔙 بازگشت", callback_data="my_subs")]]
    await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def gen_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sub_id = update.callback_query.data.split("_")[1]
    conn = sqlite3.connect(DB_NAME); link = conn.execute('SELECT link FROM subs WHERE id=?', (sub_id,)).fetchone()[0]; conn.close()
    qr = qrcode.make(link); bio = BytesIO(); qr.save(bio, 'PNG'); bio.seek(0)
    await context.bot.send_photo(chat_id=update.callback_query.message.chat_id, photo=bio, caption="Scan to connect")

# --- اجرای نهایی ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^start$"))
    app.add_handler(CallbackQueryHandler(buy_new, pattern="^buy_new$"))
    app.add_handler(CallbackQueryHandler(select_pay, pattern="^pay\|"))
    app.add_handler(CallbackQueryHandler(pay_wallet, pattern="^pay_wallet$"))
    app.add_handler(CallbackQueryHandler(my_subs, pattern="^my_subs$"))
    app.add_handler(CallbackQueryHandler(show_sub_detail, pattern="^show_sub_"))
    app.add_handler(CallbackQueryHandler(gen_qr, pattern="^genqr_"))
    
    print("ربات با موفقیت استارت شد...")
    app.run_polling()
