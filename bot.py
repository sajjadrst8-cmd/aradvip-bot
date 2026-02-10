import logging
import sqlite3
import random
import string
from datetime import datetime
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from persiantools.jdatetime import JalaliDateTime

# تنظیمات ربات
API_TOKEN = '8584319269:AAHT2fLxyC303MCl-jndJVSO7F27YO0hIAA'
ADMIN_ID = 863961919  # آیدی عددی خودت را اینجا بزن
CARD_NUMBER = "5057851560122222"
CARD_NAME = "سجاد رستگاران"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- بخش دیتابیس ---
def init_db():
    conn = sqlite3.connect('arad_bot.db')
    cursor = conn.cursor()
    # جدول کاربران
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, wallet REAL DEFAULT 0, 
                       referred_by INTEGER, join_date TEXT, status TEXT DEFAULT 'کاربر عادی')''')
    # جدول فاکتورها
    cursor.execute('''CREATE TABLE IF NOT EXISTS invoices 
                      (id TEXT PRIMARY KEY, user_id INTEGER, amount REAL, plan_info TEXT, 
                       status TEXT, date TEXT, type TEXT, custom_username TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- کلاس‌های حالت (States) ---
class BuyState(StatesGroup):
    choosing_plan = State()
    entering_username = State()
    waiting_for_receipt = State()

class WalletState(StatesGroup):
    entering_amount = State()

# --- کیبوردهای اصلی ---
def main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add("خرید اشتراک جدید", "دریافت اشتراک تست")
    keyboard.add("اشتراک های من / فاکتور های من")
    keyboard.add("حساب کاربری")
    keyboard.add("پشتیبانی / آموزش اتصال", "وضعیت سرویس ها")
    return keyboard

# --- هندلرهای شروع ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_id
    referral_id = message.get_args() # چک کردن لینک زیرمجموعه گیری
    
    conn = sqlite3.connect('arad_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        now = JalaliDateTime.now().strftime("%Y/%m/%d - %H:%M")
        ref_by = int(referral_id) if referral_id and referral_id.isdigit() and int(referral_id) != user_id else None
        cursor.execute("INSERT INTO users (user_id, wallet, referred_by, join_date) VALUES (?, ?, ?, ?)", 
                       (user_id, 0, ref_by, now))
        conn.commit()
        if ref_by:
            try:
                await bot.send_message(ref_by, f"✅ کاربر {user_id} با کد دعوت شما وارد ربات شد.\nبا اولین خرید او، هدیه به حساب شما واریز می‌شود.")
            except: pass
            
    conn.close()
    await message.answer("لطفا یکی از گزینه های زیر رو انتخاب کنید:", reply_markup=main_menu())

# --- بخش خرید اشتراک جدید ---
@dp.message_handler(lambda message: message.text == "خرید اشتراک جدید")
async def buy_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("V2ray(تانل نیم بها+کاربرنامحدود)", "Biubiu VPN")
    keyboard.add("بازگشت")
    await message.answer("لطفا نوع اشتراک خودتون رو انتخاب کنید:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "V2ray(تانل نیم بها+کاربرنامحدود)")
async def v2ray_plans(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    plans = ["5گیگ", "10گیگ", "20گیگ", "30گیگ", "50گیگ", "100گیگ", "200گیگ", "300گیگ"]
    for plan in plans:
        keyboard.add(f"{plan} زمان نامحدود ۱۰۰ هزار تومان")
    keyboard.add("بازگشت")
    await message.answer("لطفا پلن مورد نظر خودتون رو انتخاب کنید:", reply_markup=keyboard)
    await BuyState.choosing_plan.set()

@dp.message_handler(state=BuyState.choosing_plan)
async def process_plan(message: types.Message, state: FSMContext):
    if message.text == "بازگشت":
        await state.finish()
        return await buy_start(message)
    
    await state.update_data(selected_plan=message.text)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("نام کاربری تصادفی", "لغو عملیات")
    keyboard.add("بازگشت")
    
    await message.answer("👤 لطفاً یک نام کاربری برای اشتراک وارد کنید.📌\nباید بین ۳ تا ۳۲ کاراکتر باشد و می‌تواند شامل عدد، حروف a-z و _ باشد.", reply_markup=keyboard)
    await BuyState.entering_username.set()

@dp.message_handler(state=BuyState.entering_username)
async def process_username(message: types.Message, state: FSMContext):
    if message.text == "لغو عملیات":
        await state.finish()
        return await send_welcome(message)
    
    uname = message.text
    if uname == "نام کاربری تصادفی":
        uname = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    # اعتبارسنجی نام کاربری
    if not (3 <= len(uname) <= 32) or not all(c.isalnum() or c == '_' for c in uname):
        return await message.answer("❌ نام کاربری نامعتبر است. دوباره تلاش کنید یا روی دکمه تصادفی بزنید.")

    data = await state.get_data()
    plan_text = data.get('selected_plan')
    invoice_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
    now = JalaliDateTime.now().strftime("%Y/%m/%d - %H:%M")

    # صدور فاکتور ظاهری
    invoice_msg = (
        f"✅ فاکتور شما با موفقیت ایجاد شد.\n\n"
        f"🧾 شناسه: `{invoice_id}`\n"
        f"📌 وضعیت: 🟠 در انتظار\n"
        f"💰 مبلغ: 100,000 تومان\n"
        f"📦 نوع: 🆕 اشتراک جدید\n"
        f"📆 تاریخ ثبت: {now}\n"
        f"👤 کاربر: {uname}\n\n"
        f"📦 اشتراک: {plan_text}\n"
        f"📂 گروه: تانل نیم بها 🇮🇷"
    )

    inline_kb = types.InlineKeyboardMarkup()
    inline_kb.add(types.InlineKeyboardButton("پرداخت فاکتور", callback_data=f"pay_{invoice_id}"))
    inline_kb.add(types.InlineKeyboardButton("اعمال کد تخفیف", callback_data=f"discount_{invoice_id}"))
    inline_kb.add(types.InlineKeyboardButton("لغو فاکتور", callback_data="cancel_inv"))

    await message.answer(invoice_msg, reply_markup=inline_kb, parse_mode="Markdown")
    await state.finish()

# --- بخش حساب کاربری ---
@dp.message_handler(lambda message: message.text == "حساب کاربری")
async def user_account(message: types.Message):
    user_id = message.from_id
    conn = sqlite3.connect('arad_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT wallet, status, join_date FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    
    # شمارش زیرمجموعه‌ها
    cursor.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (user_id,))
    ref_count = cursor.fetchone()[0]
    conn.close()

    msg = (
        f"👤 شناسه کاربری: `{user_id}`\n"
        f"🔐 وضعیت: {res[1]}\n"
        f"💰 موجودی کیف پول: {res[0]:,.0f} تومان\n"
        f"👥 تعداد زیرمجموعه‌ها: {ref_count}\n"
        f"📆 تاریخ عضویت: {res[2]}"
    )
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("افزایش موجودی", "زیرمجموعه گیری")
    keyboard.add("بازگشت")
    await message.answer(msg, reply_markup=keyboard, parse_mode="Markdown")

# دکمه بازگشت کلی
@dp.message_handler(lambda message: message.text == "بازگشت")
async def back_to_main(message: types.Message):
    await send_welcome(message)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
# --- ادامه کدهای قبلی ---

# --- بخش پرداخت فاکتور (Callback Query) ---
@dp.callback_query_handler(lambda c: c.data.startswith('pay_'))
async def process_payment_option(callback_query: types.CallbackQuery):
    invoice_id = callback_query.data.split('_')[1]
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("💳 کارت به کارت", callback_data=f"method_card_{invoice_id}"),
        types.InlineKeyboardButton("💰 کیف پول", callback_data=f"method_wallet_{invoice_id}"),
        types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_invoice")
    )
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="لطفا روش پرداخت خود را انتخاب کنید:",
        reply_markup=keyboard
    )

# --- پرداخت با کارت به کارت ---
@dp.callback_query_handler(lambda c: c.data.startswith('method_card_'))
async def card_payment(callback_query: types.CallbackQuery, state: FSMContext):
    invoice_id = callback_query.data.split('_')[2]
    
    msg = (
        f"لطفا مبلغ را به شماره کارت زیر واریز کرده و **تصویر رسید** را اینجا ارسال کنید:\n\n"
        f"💳 شماره کارت: `{CARD_NUMBER}`\n"
        f"👤 بنام: {CARD_NAME}\n"
        f"💰 مبلغ: (طبق فاکتور)\n\n"
        f"⚠️ برای لغو روی دکمه لغو عملیات بزنید."
    )
    
    await bot.send_message(callback_query.from_user.id, msg, parse_mode="Markdown")
    await BuyState.waiting_for_receipt.set()
    await state.update_data(current_inv=invoice_id)

# --- دریافت رسید و ارسال برای ادمین ---
@dp.message_handler(content_types=['photo'], state=BuyState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    inv_id = data.get('current_inv')
    
    # ارسال به کاربر
    await message.answer("✅ تصویر شما با موفقیت ارسال شد.\nلطفا منتظر تأیید رسید باشید (کمتر از ۱۰ دقیقه).", 
                         reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("منوی اصلی"))
    
    # ارسال برای ادمین
    admin_kb = types.InlineKeyboardMarkup()
    admin_kb.add(
        types.InlineKeyboardButton("✅ تایید", callback_data=f"confirm_{message.from_user.id}_{inv_id}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{message.from_user.id}")
    )
    
    await bot.send_photo(
        ADMIN_ID, 
        message.photo[-1].file_id, 
        caption=f"🔔 رسید جدید!\n👤 کاربر: {message.from_user.id}\n🧾 فاکتور: {inv_id}",
        reply_markup=admin_kb
    )
    await state.finish()

# --- تایید نهایی توسط ادمین ---
@dp.callback_query_handler(lambda c: c.data.startswith('confirm_'))
async def admin_confirm(callback_query: types.CallbackQuery):
    _, user_id, inv_id = callback_query.data.split('_')
    
    # اینجا باید اشتراک در دیتابیس فعال شود
    await bot.send_message(user_id, "🎉 رسید شما تأیید شد!\nبرای مشاهده اطلاعات اشتراک به 'اشتراک های من' مراجعه کنید.")
    await callback_query.answer("تایید شد ✅")
    await bot.edit_message_caption(ADMIN_ID, callback_query.message.message_id, caption="این رسید تایید شد ✅")

# --- بخش Biubiu VPN ---
@dp.message_handler(lambda message: message.text == "Biubiu VPN")
async def biubiu_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("تک کاربره", "دو کاربره")
    keyboard.add("بازگشت")
    await message.answer("لطفا نوع اشتراک Biubiu را انتخاب کنید:", reply_markup=keyboard)

# --- تعرفه‌های دقیق Biubiu ---
@dp.message_handler(lambda message: message.text in ["تک کاربره", "دو کاربره"])
async def biubiu_plans(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if message.text == "تک کاربره":
        plans = [
            "1ماهه حجم نامحدود (تک) - 100,000 تومان",
            "2ماهه حجم نامحدود (تک) - 200,000 تومان",
            "3ماهه حجم نامحدود (تک) - 300,000 تومان"
        ]
    else: # دو کاربره
        plans = [
            "1ماهه حجم نامحدود (دو) - 300,000 تومان",
            "3ماهه حجم نامحدود (دو) - 600,000 تومان",
            "6ماهه حجم نامحدود (دو) - 1,100,000 تومان",
            "12ماهه حجم نامحدود (دو) - 1,800,000 تومان"
        ]
    
    for plan in plans:
        keyboard.add(plan)
    keyboard.add("بازگشت")
    
    await state.update_data(product_type="Biubiu") # ذخیره نوع محصول
    await message.answer(f"📦 تعرفه‌های {message.text} Biubiu:", reply_markup=keyboard)
    await BuyState.choosing_plan.set()

# --- اصلاح هندلر پردازش پلن برای داینامیک کردن قیمت فاکتور ---
@dp.message_handler(state=BuyState.choosing_plan)
async def process_plan(message: types.Message, state: FSMContext):
    if message.text == "بازگشت":
        await state.finish()
        return await buy_start(message)
    
    # استخراج قیمت از متن دکمه (مثلاً 100,000)
    import re
    price_search = re.search(r"([\d,]+) تومان", message.text)
    price = price_search.group(1) if price_search else "نامشخص"
    
    await state.update_data(selected_plan=message.text, plan_price=price)
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("نام کاربری تصادفی", "لغو عملیات")
    keyboard.add("بازگشت")
    
    await message.answer("👤 لطفاً یک نام کاربری برای اشتراک وارد کنید.\n(بین ۳ تا ۳۲ کاراکتر، حروف انگلیسی و عدد)", reply_markup=keyboard)
    await BuyState.entering_username.set()

# --- بخش زیرمجموعه گیری (تکمیل شده) ---
@dp.message_handler(lambda message: message.text == "زیرمجموعه گیری")
async def referral_link(message: types.Message):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    
    msg = (
        f"🔗 لینک اختصاصی دعوت شما:\n{ref_link}\n\n"
        f"🎁 دوستان خود را دعوت کنید و 10 درصد از مبلغ خرید آن‌ها را به عنوان هدیه در کیف پول دریافت کنید!"
    )
    await message.answer(msg, reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("بازگشت"))

# --- بخش پشتیبانی و آموزش ---
@dp.message_handler(lambda message: message.text == "پشتیبانی / آموزش اتصال")
async def support_section(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📚 کانال آموزش", url="https://t.me/AradVIPTeaching"))
    
    msg = "📞 برای ارتباط با پشتیبانی:\n@AradVIP\n\nبرای آموزش‌ها روی دکمه زیر کلیک کنید."
    await message.answer(msg, reply_markup=keyboard)

# --- وضعیت سرویس‌ها ---
@dp.message_handler(lambda message: message.text == "وضعیت سرویس ها")
async def service_status(message: types.Message):
    url = "http://v2inj.galexystore.ir:3001/"
    await message.answer(f"🌐 وضعیت لحظه‌ای سرویس‌ها:\n{url}")
