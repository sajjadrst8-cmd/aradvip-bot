import logging
import sqlite3
import re
import random
import string
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# ================= تنظیمات اصلی =================
API_TOKEN = '8584319269:AAHaP6fBhFX5N4qwPVCqmUleLkNmWZi7MYk' 
ADMIN_ID = 863961919  # آیدی عددی خودت
CARD_NUMBER = "5057851560122222"
CARD_NAME = "سجاد رستگاران"
SUPPORT_ID = "@AradVIP"
TEACHING_LINK = "https://t.me/AradVIPTeaching"
STATUS_LINK = "http://v2inj.galexystore.ir:3001/"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ================= دیتابیس =================
conn = sqlite3.connect('v2ray_pro.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, 
                   referred_by INTEGER, joined_date TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS invoices 
                  (id TEXT PRIMARY KEY, user_id INTEGER, amount INTEGER, 
                   type TEXT, status TEXT, date TEXT, plan_name TEXT, alias TEXT)''')
conn.commit()

# ================= حالات =================
class BotStates(StatesGroup):
    entering_username = State()
    sending_receipt = State()

# ================= منوها =================
def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("خرید اشتراک جدید", "دریافت اشتراک تست")
    markup.add("اشتراک های من / فاکتور های من")
    markup.add("حساب کاربری")
    markup.add("پشتیبانی / آموزش اتصال", "وضعیت سرویس ها")
    return markup

# ================= هندلرها =================
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    uid = message.from_user.id
    ref_id = message.get_args()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not cursor.fetchone():
        referrer = int(ref_id) if ref_id and ref_id.isdigit() else None
        cursor.execute("INSERT INTO users VALUES (?, 0, ?, ?)", (uid, referrer, datetime.now().strftime("%Y/%m/%d")))
        conn.commit()
    await message.answer(f"سلام {message.from_user.first_name} عزیز، به ربات خوش آمدید!", reply_markup=get_main_menu())

# --- منوی خرید ---
@dp.message_handler(lambda m: m.text == "خرید اشتراک جدید")
async def buy_menu(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("V2ray(تانل نیم بها+کاربرنامحدود)", "Biubiu VPN")
    markup.add("بازگشت")
    await message.answer("نوع اشتراک خود را انتخاب کنید:", reply_markup=markup)

# --- انتخاب نوع کاربر Biubiu ---
@dp.message_handler(lambda m: m.text == "Biubiu VPN")
async def biubiu_user_type(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("تک کاربره 👤", "دو کاربره 👥")
    markup.add("بازگشت")
    await message.answer("لطفاً نوع اشتراک Biubiu را انتخاب کنید:", reply_markup=markup)

# --- تعرفه‌های Biubiu تک کاربره ---
@dp.message_handler(lambda m: m.text == "تک کاربره 👤")
async def biubiu_single(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    plans = [
        "Biubiu تک‌کاربره - ۱ ماهه (۷۰ هزار تومان)",
        "Biubiu تک‌کاربره - ۳ ماهه (۱۸۰ هزار تومان)",
        "Biubiu تک‌کاربره - ۶ ماهه (۳۴۰ هزار تومان)",
        "Biubiu تک‌کاربره - یکساله (۶۰۰ هزار تومان)"
    ]
    for p in plans: markup.add(p)
    markup.add("بازگشت")
    await message.answer("پلن تک‌کاربره مورد نظر را انتخاب کنید:", reply_markup=markup)

# --- تعرفه‌های Biubiu دو کاربره ---
@dp.message_handler(lambda m: m.text == "دو کاربره 👥")
async def biubiu_double(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    plans = [
        "Biubiu دو‌کاربره - ۱ ماهه (۱۰۰ هزار تومان)",
        "Biubiu دو‌کاربره - ۳ ماهه (۲۸۰ هزار تومان)",
        "Biubiu دو‌کاربره - ۶ ماهه (۵۰۰ هزار تومان)",
        "Biubiu دو‌کاربره - یکساله (۹۰۰ هزار تومان)"
    ]
    for p in plans: markup.add(p)
    markup.add("بازگشت")
    await message.answer("پلن دو‌کاربره مورد نظر را انتخاب کنید:", reply_markup=markup)

# --- تعرفه‌های V2ray ---
@dp.message_handler(lambda m: m.text == "V2ray(تانل نیم بها+کاربرنامحدود)")
async def v2ray_plans(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    v2_plans = ["5گیگ", "10گیگ", "20گیگ", "30گیگ", "50گیگ", "100گیگ", "200گیگ", "300گیگ"]
    for p in v2_plans: markup.insert(f"{p} زمان نامحدود ۱۰۰ هزار تومان")
    markup.add("بازگشت")
    await message.answer("پلن V2ray مورد نظر را انتخاب کنید:", reply_markup=markup)

# --- نام کاربری و صدور فاکتور (هوشمند برای تمام مبالغ) ---
@dp.message_handler(lambda m: "تومان" in m.text)
async def ask_username(message: types.Message, state: FSMContext):
    # استخراج مبلغ با استفاده از اعداد انگلیسی/فارسی موجود در متن دکمه
    price_search = re.findall(r'(\d+(?:[\d,]*\d))', message.text.replace('،', ''))
    price = 0
    if price_search:
        # تبدیل قیمت فارسی به انگلیسی و حذف کاما
        raw_price = price_search[-1].replace(',', '')
        price = int(raw_price) * 1000 if int(raw_price) < 2000 else int(raw_price) # تشخیص هزار تومان
    
    await state.update_data(plan=message.text, price=price)
    markup = ReplyKeyboardMarkup(resize_keyboard=True).add("انتخاب نام تصادفی", "بازگشت")
    await message.answer("👤 نام کاربری اشتراک را وارد کنید (۳ تا ۳۲ کاراکتر):", reply_markup=markup)
    await BotStates.entering_username.set()

@dp.message_handler(state=BotStates.entering_username)
async def create_invoice(message: types.Message, state: FSMContext):
    if message.text == "بازگشت":
        await state.finish()
        return await start_cmd(message)
    
    uname = message.text
    if uname == "انتخاب نام تصادفی":
        uname = f"{message.from_user.id}1244"
    
    if not re.match(r"^[a-z0-9_]{3,32}$", uname.lower()):
        return await message.answer("❌ نام کاربری غیرمجاز است. (فقط حروف انگلیسی، عدد و _)")

    data = await state.get_data()
    inv_id = "".join(random.choices(string.digits, k=10))
    
    cursor.execute("INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (inv_id, message.from_user.id, data['price'], "خرید اشتراک", "🟠 در انتظار", 
                    datetime.now().strftime("%Y/%m/%d"), data['plan'], uname))
    conn.commit()

    text = f"📑 فاکتور شماره: {inv_id}\n💰 مبلغ: {data['price']:,} تومان\n📦 سرویس: {data['plan']}\n👤 یوزرنیم: {uname}\n\nجهت تکمیل خرید، روی پرداخت کلیک کنید."
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton("💳 پرداخت کارت به کارت", callback_data=f"pay_{inv_id}"))
    await message.answer(text, reply_markup=markup)
    await state.finish()

# --- سیستم زیرمجموعه‌گیری ---
@dp.message_handler(lambda m: m.text == "زیرمجموعه گیری")
async def referral_sys(message: types.Message):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    text = f"👥 برنامه کسب درآمد\n\nبا دعوت دوستان خود، 10% از هر خرید آن‌ها را در کیف پول خود دریافت کنید!\n\n🔗 لینک دعوت شما:\n`{ref_link}`"
    await message.answer(text, parse_mode="Markdown")

# --- پرداخت و تایید ادمین ---
@dp.callback_query_handler(lambda c: c.data.startswith('pay_'))
async def process_pay(callback: types.CallbackQuery, state: FSMContext):
    inv_id = callback.data.split('_')[1]
    await state.update_data(current_inv=inv_id)
    await callback.message.answer(f"لطفا مبلغ را به کارت زیر واریز کرده و عکس رسید را بفرستید:\n\n💳 {CARD_NUMBER}\n👤 {CARD_NAME}")
    await BotStates.sending_receipt.set()

@dp.message_handler(content_types=['photo'], state=BotStates.sending_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    inv_id = data['current_inv']
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ تایید", callback_data=f"ok_{inv_id}"),
        InlineKeyboardButton("❌ رد", callback_data=f"no_{inv_id}")
    )
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"فیش جدید از {message.from_user.id}\nفاکتور: {inv_id}", reply_markup=markup)
    await message.answer("⏳ رسید برای مدیریت ارسال شد و در حال بررسی است.")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith('ok_') or c.data.startswith('no_'))
async def admin_decision(callback: types.CallbackQuery):
    action, inv_id = callback.data.split('_')
    cursor.execute("SELECT user_id, amount FROM invoices WHERE id=?", (inv_id,))
    res = cursor.fetchone()
    if not res: return
    
    uid, amt = res
    if action == "ok":
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amt, uid))
        cursor.execute("UPDATE invoices SET status = 'تایید شده' WHERE id = ?", (inv_id,))
        # پرداخت سود معرف
        cursor.execute("SELECT referred_by FROM users WHERE user_id=?", (uid,))
        ref = cursor.fetchone()[0]
        if ref:
            bonus = int(amt * 0.1)
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (bonus, ref))
            try: await bot.send_message(ref, f"💰 هدیه ۱۰٪ واریز شد! ({bonus} تومان)")
            except: pass
        conn.commit()
        await bot.send_message(uid, "✅ فیش شما تایید شد و موجودی اعمال گردید!")
        await callback.message.edit_caption("✅ این فیش تایید شد.")
    else:
        await bot.send_message(uid, "❌ فیش شما توسط ادمین رد شد. اگر خطایی رخ داده به پشتیبانی پیام دهید.")
        await callback.message.edit_caption("❌ رد شد.")

@dp.message_handler(lambda m: m.text == "بازگشت")
async def back_to_main(message: types.Message):
    await start_cmd(message)

# --- مدیریت دستی ادمین ---
@dp.message_handler(commands=['charge'], user_id=ADMIN_ID)
async def manual_charge(message: types.Message):
    try:
        _, uid, amt = message.text.split()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amt, uid))
        conn.commit()
        await message.answer(f"✅ مبلغ {amt} با موفقیت به حساب {uid} اضافه شد.")
    except:
        await message.answer("فرمت صحیح: /charge 12345 50000")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
