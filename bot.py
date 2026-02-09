import sqlite3
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- تنظیمات مرزبان ---
MARZBAN_URL = "https://v2inj.galexystore.ir" # آدرس پنل شما
MARZBAN_ADMIN_USER = "1804445169" # یوزرنیم پنل را اینجا بزن
MARZBAN_ADMIN_PASS = "1804445169" # پسورد پنل را اینجا بزن

# --- تنظیمات ربات ---
TOKEN = "8531397872:AAEi36WyX5DOW_GLk6yL44bHVjx0jw2pVn4"
ADMIN_ID = 863961919 
CARD_NUMBER = "6037-9999-8888-7777"
CARD_NAME = "سجاد رستگاران"
DB_NAME = "bot_data.db"

# --- توابع اتصال به API مرزبان ---
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
    
    # استخراج حجم از نام پلن (مثلا "5 گیگ" -> 5)
    import re
    digits = re.findall(r'\d+', plan_name)
    gb_limit = int(digits[0]) if digits else 0
    bytes_limit = gb_limit * 1024 * 1024 * 1024
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    username = f"tg_{user_id}_{sqlite3.connect(DB_NAME).execute('SELECT COUNT(*) FROM subs').fetchone()[0]}"
    
    payload = {
        "username": username,
        "proxies": {"vless": {}, "vmess": {}}, # هر دو را فعال میکند
        "data_limit": bytes_limit,
        "expire": 0 
    }
    
    try:
        url = f"{MARZBAN_URL}/api/user"
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get('subscription_url'), username
    except: return None, None

# --- مدیریت دیتابیس ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS subs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan TEXT, link TEXT, username TEXT)')
    conn.commit(); conn.close()

init_db()

# --- منوها و هندلرها ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("💳 خرید اشتراک جدید", callback_data="buy_new")],
          [InlineKeyboardButton("📋 اشتراک‌های من", callback_data="my_subs")],
          [InlineKeyboardButton("👤 حساب و شارژ", callback_data="account")]]
    text = "به ربات خوش آمدید. یکی از گزینه‌ها را انتخاب کنید:"
    if update.message: await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else: await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

# (توابع list_v2ray و list_biubiu مشابه قبل هستند...)

async def pay_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id
    order = context.user_data.get('order')
    conn = sqlite3.connect(DB_NAME)
    bal = conn.execute('SELECT balance FROM users WHERE user_id=?', (uid,)).fetchone()[0]
    
    if bal >= order['price']:
        # ساخت مستقیم در مرزبان
        sub_url, uname = create_marzban_user(uid, order['name'])
        if sub_url:
            conn.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (order['price'], uid))
            conn.execute('INSERT INTO subs (user_id, plan, link, username) VALUES (?, ?, ?, ?)', (uid, order['name'], sub_url, uname))
            conn.commit()
            await update.callback_query.message.edit_text(f"✅ پرداخت موفق!\nاشتراک {order['name']} فعال شد.\nبرای دریافت لینک به 'اشتراک‌های من' بروید.")
        else:
            await update.callback_query.answer("❌ خطا در ساخت اکانت در پنل!", show_alert=True)
    else:
        await update.callback_query.answer("❌ موجودی کافی نیست!", show_alert=True)
    conn.close()

async def admin_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    uid = int(data.split("_")[1])
    if data.startswith("ok_"):
        # در اینجا فرض میکنیم ادمین تایید کرده، پس اکانت ساخته شود
        # توجه: باید اطلاعات پکیج انتخابی کاربر را ذخیره کرده باشید
        # برای سادگی اینجا 10 گیگ فرض میکنیم (میتوانید شخصی سازی کنید)
        sub_url, uname = create_marzban_user(uid, "10 گیگ") 
        if sub_url:
            conn = sqlite3.connect(DB_NAME)
            conn.execute('INSERT INTO subs (user_id, plan, link, username) VALUES (?, ?, ?, ?)', (uid, "10 گیگ تایید شده", sub_url, uname))
            conn.commit(); conn.close()
            await context.bot.send_message(uid, "✅ رسید تایید شد! اشتراک شما ساخته شد.")
            await update.callback_query.edit_message_caption("🟢 ساخته شد.")
    else:
        await context.bot.send_message(uid, "❌ رسید رد شد.")

# (بقیه کدها شامل my_subs و handle_receipt مشابه نسخه قبلی)

app = ApplicationBuilder().token(TOKEN).build()
# اضافه کردن هندلرها...
app.run_polling()
