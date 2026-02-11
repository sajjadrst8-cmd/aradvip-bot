import logging
import sqlite3
import random
import string
import re
from datetime import datetime
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from persiantools.jdatetime import JalaliDateTime

# --- تنظیمات اصلی ---
API_TOKEN = '8584319269:AAHT2fLxyC303MCl-jndJVSO7F27YO0hIAA'
ADMIN_ID = 863961919  
CARD_NUMBER = "5057851560122222"
CARD_NAME = "سجاد رستگاران"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- دیتابیس ---
def init_db():
    conn = sqlite3.connect('arad_bot.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, wallet REAL DEFAULT 0, 
                       referred_by INTEGER, join_date TEXT, status TEXT DEFAULT 'کاربر عادی')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS invoices 
                      (id TEXT PRIMARY KEY, user_id INTEGER, amount TEXT, plan_info TEXT, 
                       status TEXT, date TEXT, type TEXT, custom_username TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- حالات (States) ---
class BuyState(StatesGroup):
    choosing_plan = State()
    entering_username = State()
    waiting_for_receipt = State()

# --- کیبورد اصلی ---
def main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add("خرید اشتراک جدید", "دریافت اشتراک تست")
    keyboard.add("اشتراک های من / فاکتور های من")
    keyboard.add("حساب کاربری")
    keyboard.add("پشتیبانی / آموزش اتصال", "وضعیت سرویس ها")
    return keyboard

# --- هندلر شروع ---
@dp.message_handler(commands=['start'], state="*")
async def send_welcome(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_id
    conn = sqlite3.connect('arad_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        now = JalaliDateTime.now().strftime("%Y/%m/%d - %H:%M")
        cursor.execute("INSERT INTO users (user_id, wallet, join_date) VALUES (?, ?, ?)", (user_id, 0, now))
        conn.commit()
    conn.close()
    await message.answer("🌹 به ربات آراد وی‌آی‌پی خوش آمدید!\nلطفاً یک گزینه را انتخاب کنید:", reply_markup=main_menu())

# --- بخش خرید اصلی ---
@dp.message_handler(lambda message: message.text == "خرید اشتراک جدید")
async def buy_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("V2ray (تانل نیم بها)", "Biubiu VPN")
    keyboard.add("بازگشت")
    await message.answer("لطفا نوع سرویس مورد نظر را انتخاب کنید:", reply_markup=keyboard)

# --- منوی Biubiu VPN ---
@dp.message_handler(lambda message: "Biubiu" in message.text)
async def biubiu_menu(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("تک کاربره (Biubiu)", "دو کاربره (Biubiu)")
    keyboard.add("بازگشت")
    await message.answer("لطفا نوع اشتراک Biubiu را انتخاب کنید:", reply_markup=keyboard)

# --- تعرفه‌های Biubiu (اصلاح شده) ---
@dp.message_handler(lambda message: "تک کاربره" in message.text or "دو کاربره" in message.text)
async def biubiu_plans(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    
    if "تک" in message.text:
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
    
    for p in plans:
        keyboard.add(p)
    keyboard.add("بازگشت")
    
    await message.answer(f"📦 تعرفه‌های {message.text}:", reply_markup=keyboard)
    await BuyState.choosing_plan.set()

# --- تعرفه‌های V2ray ---
@dp.message_handler(lambda message: "V2ray" in message.text)
async def v2ray_plans(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    plans = ["5گیگ", "10گیگ", "20گیگ", "30گیگ", "50گیگ", "100گیگ"]
    for p in plans: keyboard.add(f"{p} زمان نامحدود - 100,000 تومان")
    keyboard.add("بازگشت")
    await message.answer("لطفا پلن V2ray را انتخاب کنید:", reply_markup=keyboard)
    await BuyState.choosing_plan.set()

# --- پردازش انتخاب پلن و دریافت نام کاربری ---
@dp.message_handler(state=BuyState.choosing_plan)
async def process_plan_choice(message: types.Message, state: FSMContext):
    if message.text == "بازگشت":
        await state.finish()
        return await buy_start(message)
    
    price_match = re.search(r"([\d,]+) تومان", message.text)
    price = price_match.group(1) if price_match else "100,000"
    
    await state.update_data(selected_plan=message.text, plan_price=price)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("نام کاربری تصادفی", "لغو عملیات")
    await message.answer("👤 یک نام کاربری (انگلیسی) برای اکانت وارد کنید:", reply_markup=keyboard)
    await BuyState.entering_username.set()

@dp.message_handler(state=BuyState.entering_username)
async def process_username(message: types.Message, state: FSMContext):
    if message.text == "لغو عملیات":
        await state.finish()
        return await send_welcome(message, state)
    
    uname = message.text
    if uname == "نام کاربری تصادفی":
        uname = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    data = await state.get_data()
    inv_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    invoice_msg = (
        f"✅ فاکتور پرداخت\n\n"
        f"🧾 شناسه فاکتور: `{inv_id}`\n"
        f"📦 سرویس: {data.get('selected_plan')}\n"
        f"👤 کاربر: `{uname}`\n"
        f"💰 مبلغ قابل پرداخت: {data.get('plan_price')} تومان\n\n"
        f"👇 جهت تکمیل خرید، روی دکمه پرداخت کلیک کنید."
    )
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💳 کارت به کارت", callback_data=f"pay_card_{inv_id}_{data.get('plan_price')}"))
    kb.add(types.InlineKeyboardButton("❌ لغو", callback_data="cancel_inv"))
    
    await message.answer(invoice_msg, reply_markup=kb, parse_mode="Markdown")
    await state.finish()

# --- هندلرهای دکمه‌های بازگشت و لغو ---
@dp.message_handler(lambda message: message.text == "بازگشت", state="*")
async def general_back(message: types.Message, state: FSMContext):
    await state.finish()
    await send_welcome(message, state)

@dp.callback_query_handler(lambda c: c.data == "cancel_inv")
async def cancel_invoice_cb(callback: types.CallbackQuery):
    await callback.message.edit_text("❌ فاکتور لغو شد.")

# --- فرآیند پرداخت کارت به کارت ---
@dp.callback_query_handler(lambda c: c.data.startswith('pay_card_'))
async def card_pay_info(callback: types.CallbackQuery, state: FSMContext):
    _, _, inv_id, price = callback.data.split('_')
    msg = (
        f"💳 شماره کارت: `{CARD_NUMBER}`\n"
        f"👤 بنام: {CARD_NAME}\n"
        f"💰 مبلغ: {price} تومان\n\n"
        f"📸 لطفاً پس از واریز، **عکس رسید** را اینجا بفرستید."
    )
    await bot.send_message(callback.from_user.id, msg, parse_mode="Markdown")
    await BuyState.waiting_for_receipt.set()
    await state.update_data(current_inv=inv_id)

@dp.message_handler(content_types=['photo'], state=BuyState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.answer("✅ رسید دریافت شد و برای ادمین ارسال گردید. منتظر تایید بمانید.")
    
    admin_kb = types.InlineKeyboardMarkup()
    admin_kb.add(types.InlineKeyboardButton("✅ تایید", callback_data=f"adm_confirm_{message.from_user.id}"))
    admin_kb.add(types.InlineKeyboardButton("❌ رد", callback_data=f"adm_reject_{message.from_user.id}"))
    
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"🔔 رسید جدید\nکاربر: {message.from_user.id}\nفاکتور: {data.get('current_inv')}", 
                         reply_markup=admin_kb)
    await state.finish()

# --- پاسخ ادمین ---
@dp.callback_query_handler(lambda c: c.data.startswith('adm_'))
async def admin_action(callback: types.CallbackQuery):
    action, _, user_id = callback.data.split('_')[0], callback.data.split('_')[1], callback.data.split('_')[2]
    if action == "confirm":
        await bot.send_message(user_id, "✅ رسید شما تایید شد! اشتراک شما به زودی فعال می‌شود.")
        await callback.answer("تایید شد")
    else:
        await bot.send_message(user_id, "❌ رسید شما رد شد. لطفا با پشتیبانی در ارتباط باشید.")
        await callback.answer("رد شد")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
