import psycopg2
import requests
import re
import os
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

# اتصال به دیتابیس PostgreSQL در Railway
# لینک را از پنل ریلوِی کپی کن و اینجا بذار
DATABASE_URL = "postgresql://postgres:lsiRZhVlzjnTlcBiNzdOLoRuSHsFpDCP@maglev.proxy.rlwy.net:15760/railway"

V2RAY_SUBS = [
    {"name": "5 گیگ", "price": 60000},
    {"name": "10 گیگ", "price": 100000},
    {"name": "20 گیگ", "price": 150000}
]

# --- توابع مدیریت دیتابیس ---
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (user_id BIGINT PRIMARY KEY, balance INTEGER DEFAULT 0)')
    cur.execute('CREATE TABLE IF NOT EXISTS subs (id SERIAL PRIMARY KEY, user_id BIGINT, plan TEXT, link TEXT, username TEXT)')
    conn.commit()
    cur.close()
    conn.close()

init_db()

# --- تنظیمات مرزبان ---
MARZBAN_URL = "https://v2inj.galexystore.ir"
MARZBAN_ADMIN_USER = "1804445169" # یوزرنیم ادمین پنل
MARZBAN_ADMIN_PASS = "1804445169" # پسورد ادمین پنل

def get_marzban_token():
    # لیست آدرس‌هایی که ممکن است API روی آن‌ها باشد را تست می‌کنیم
    potential_urls = [
        f"{MARZBAN_URL}/api/admin/token",
        f"{MARZBAN_URL}:443/api/admin/token"
    ]
    
    for url in potential_urls:
        try:
            print(f"Trying to connect to: {url}")
            data = {'username': MARZBAN_ADMIN_USER, 'password': MARZBAN_ADMIN_PASS}
            # زمان انتظار را بیشتر کردیم (30 ثانیه)
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                print("Successfully connected to Marzban!")
                return response.json().get('access_token')
            else:
                print(f"Status Code {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Connection failed for {url}: {e}")
            
    return None

def create_marzban_user(user_id, plan_name):
    token = get_marzban_token()
    if not token:
        print("Failed to get Marzban Token")
        return None, None

    # استخراج حجم از اسم پلن
    try:
        gb = int(re.findall(r'\d+', plan_name)[0])
    except:
        gb = 10 
    
    bytes_limit = gb * 1024 * 1024 * 1024
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # اصلاح بخش زمان که ارور می‌داد
    import time 
    username = f"tg_{user_id}_{int(time.time())}"
    
    payload = {
        "username": username,
        "proxies": {"vless": {}, "vmess": {},  {}},
        "data_limit": bytes_limit,
        "expire": 0
    }
    
    try:
        res = requests.post(f"{MARZBAN_URL}/api/user", json=payload, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json().get('subscription_url'), username
        else:
            print(f"Marzban Error: {res.text}")
    except Exception as e:
        print(f"Request Error: {e}")
    
    return None, None


# --- هندلرهای تلگرام ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM users WHERE user_id=%s', (uid,))
    if not cur.fetchone():
        cur.execute('INSERT INTO users (user_id) VALUES (%s)', (uid,))
        conn.commit()
    cur.close()
    conn.close()
    kb = [[InlineKeyboardButton("💳 خرید اشتراک جدید", callback_data="buy_new")],
          [InlineKeyboardButton("📋 اشتراک‌های من", callback_data="my_subs")],
          [InlineKeyboardButton("👤 حساب و شارژ", callback_data="account")]]
    text = "🚀 به ربات فروش فیلترشکن خوش آمدید!"
    if update.message: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else: await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def account_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT balance FROM users WHERE user_id=%s', (uid,))
    bal = cur.fetchone()[0]
    cur.close()
    conn.close()
    text = f"👤 حساب شما:\n💰 موجودی: {bal:,} تومان"
    kb = [[InlineKeyboardButton("➕ شارژ کیف پول", callback_data="pay_card")],
          [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def buy_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(f"{p['name']} - {p['price']:,} تومان", callback_data=f"sel|{p['price']}|{p['name']}")] for p in V2RAY_SUBS]
    kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="start")])
    await update.callback_query.message.edit_text("لطفاً پکیج را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

async def select_pay_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, price, name = update.callback_query.data.split("|")
    context.user_data['order'] = {"price": int(price), "name": name}
    kb = [[InlineKeyboardButton("💰 پرداخت از کیف پول", callback_data="pay_wallet")],
          [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")]]
    await update.callback_query.message.edit_text(f"سرویس: {name}\nقیمت: {int(price):,} تومان", reply_markup=InlineKeyboardMarkup(kb))

async def pay_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id
    order = context.user_data.get('order')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT balance FROM users WHERE user_id=%s', (uid,))
    bal = cur.fetchone()[0]
    if bal >= order['price']:
        sub_url, uname = create_marzban_user(uid, order['name'])
        if sub_url:
            cur.execute('UPDATE users SET balance = balance - %s WHERE user_id = %s', (order['price'], uid))
            cur.execute('INSERT INTO subs (user_id, plan, link, username) VALUES (%s, %s, %s, %s)', (uid, order['name'], sub_url, uname))
            conn.commit()
            await update.callback_query.message.edit_text("✅ موفق! از بخش 'اشتراک‌های من' لینک را دریافت کنید.")
        else:
            await update.callback_query.answer("❌ خطا در اتصال به پنل!", show_alert=True)
    else:
        await update.callback_query.answer("❌ موجودی کافی نیست!", show_alert=True)
    cur.close()
    conn.close()

async def pay_card_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"💳 واریز به:\n`{CARD_NUMBER}`\n👤 {CARD_NAME}\n\n📸 عکس رسید را بفرستید."
    await update.callback_query.message.edit_text(text, parse_mode="Markdown")

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo = update.message.photo[-1].file_id
        uid = update.message.from_user.id
        kb = [[InlineKeyboardButton("✅ تایید ۶۰ ت", callback_data=f"adm_60000_{uid}"),
               InlineKeyboardButton("✅ تایید ۱۰۰ ت", callback_data=f"adm_100000_{uid}")],
              [InlineKeyboardButton("❌ رد", callback_data=f"adm_reject_{uid}")]]
        await context.bot.send_photo(ADMIN_ID, photo, caption=f"رسید از: {uid}", reply_markup=InlineKeyboardMarkup(kb))
        await update.message.reply_text("⏳ رسید برای ادمین ارسال شد.")

async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data.split("_")
    action, target_uid = data[1], int(data[2])
    conn = get_db_connection()
    cur = conn.cursor()
    if action == "reject":
        await context.bot.send_message(target_uid, "❌ رسید رد شد.")
    else:
        amount = int(action)
        cur.execute('UPDATE users SET balance = balance + %s WHERE user_id = %s', (amount, target_uid))
        conn.commit()
        await context.bot.send_message(target_uid, f"✅ حساب شما {amount:,} شارژ شد.")
    cur.close()
    conn.close()
    await update.callback_query.edit_message_caption("انجام شد.")

async def my_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, plan FROM subs WHERE user_id=%s', (uid,))
    subs = cur.fetchall()
    cur.close()
    conn.close()
    if not subs:
        await update.callback_query.message.edit_text("اشتراکی ندارید.")
        return
    kb = [[InlineKeyboardButton(f"📦 {s[1]}", callback_data=f"show_{s[0]}")] for s in subs]
    await update.callback_query.message.edit_text("اشتراک‌های شما:", reply_markup=InlineKeyboardMarkup(kb))

async def show_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid = update.callback_query.data.split("_")[1]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT plan, link, username FROM subs WHERE id=%s', (sid,))
    sub = cur.fetchone()
    cur.close()
    conn.close()
    await update.callback_query.message.edit_text(f"📋 {sub[0]}\n🔗 `{sub[1]}`", parse_mode="Markdown")

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
    app.run_polling()
