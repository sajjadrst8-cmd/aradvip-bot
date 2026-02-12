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

# --- تنظیمات ---
API_TOKEN = '8584319269:AAHT2fLxyC303MCl-jndJVSO7F27YO0hIAA'
ADMIN_ID = 863961919  
CARD_NUMBER = "5057851560122222"
CARD_NAME = "سجاد رستگاران"
ADMIN_OFF_CODE = "ARAD2026" 
OFF_PERCENT = 20 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- دیتابیس ---
def init_db():
    conn = sqlite3.connect('arad_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, wallet REAL DEFAULT 0, 
                       referred_by INTEGER, join_date TEXT)''')
    conn.commit()
    conn.close()

init_db()

class BotState(StatesGroup):
    entering_amount = State() 
    entering_offcode = State() 
    entering_username = State()
    waiting_for_receipt = State()

# --- توابع کمکی ---
def get_user_info(user_id):
    conn = sqlite3.connect('arad_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT wallet, referred_by, join_date FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    if not data:
        now = datetime.now().strftime("%Y/%m/%d - %H:%M")
        cursor.execute("INSERT INTO users (user_id, wallet, join_date) VALUES (?, ?, ?)", (user_id, 0, now))
        conn.commit()
        data = (0, None, now)
    cursor.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (user_id,))
    ref_count = cursor.fetchone()[0]
    conn.close()
    return data, ref_count

def main_menu_inline():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🛍 خرید اشتراک جدید", callback_data="buy_menu"),
           types.InlineKeyboardButton("🎁 دریافت اشتراک تست", callback_data="get_test"))
    kb.add(types.InlineKeyboardButton("📜 اشتراک‌های من", callback_data="my_subs"),
           types.InlineKeyboardButton("🧾 فاکتورهای من", callback_data="my_invoices"))
    kb.add(types.InlineKeyboardButton("👤 حساب کاربری", callback_data="account"))
    kb.add(types.InlineKeyboardButton("📞 پشتیبانی", callback_data="support"),
           types.InlineKeyboardButton("📚 آموزش اتصال", callback_data="tutorial"))
    kb.add(types.InlineKeyboardButton("📊 وضعیت سرویس‌ها", callback_data="status"))
    return kb

# --- شروع ---
@dp.message_handler(commands=['start'], state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    get_user_info(user_id) 
    await message.answer("🌹 به ربات آراد وی‌آی‌پی خوش آمدید!", reply_markup=main_menu_inline())

# --- بخش خرید (هندلرهای کلیک روی تعرفه) ---
@dp.callback_query_handler(lambda c: c.data == "buy_menu", state="*")
async def buy_menu(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("🛰 V2ray (نیم بها + نامحدود)", callback_data="type_v2ray"),
           types.InlineKeyboardButton("🚀 Biubiu VPN", callback_data="type_biubiu"),
           types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
    await callback.message.edit_text("لطفا نوع سرویس را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "type_biubiu")
async def biubiu_select(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("👤 تک کاربره", callback_data="biu_single"),
           types.InlineKeyboardButton("👥 دو کاربره", callback_data="biu_double"),
           types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_menu"))
    await callback.message.edit_text("نوع اشتراک Biubiu را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("biu_"))
async def biubiu_plans(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    if "single" in callback.data:
        plans = [("1ماهه نامحدود (تک) - 100,000", "100000"), ("2ماهه (تک) - 200,000", "200000")]
    else:
        plans = [("1ماهه (دو) - 300,000", "300000"), ("3ماهه (دو) - 600,000", "600000")]
    for text, price in plans:
        kb.add(types.InlineKeyboardButton(f"{text} تومان", callback_data=f"set_buy_Biu_{price}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="type_biubiu"))
    await callback.message.edit_text("یک پلن را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "type_v2ray")
async def v2ray_plans(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for g in [20, 50]: # مثال برای تست
        kb.add(types.InlineKeyboardButton(f"V2ray {g} گیگ - 100,000 تومان", callback_data=f"set_buy_V2ray_{g}_100000"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_menu"))
    await callback.message.edit_text("پلن V2ray را انتخاب کنید:", reply_markup=kb)

# --- هندلر کلیک روی تعرفه و درخواست نام کاربری ---
@dp.callback_query_handler(lambda c: c.data.startswith("set_buy_"), state="*")
async def ask_username(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    # ذخیره قیمت و نام سرویس در وضعیت
    await state.update_data(p_name=data[2], p_price=data[-1], off_applied=False)
    await BotState.entering_username.set()
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🎲 نام کاربری تصادفی", callback_data="rand_user"))
    await callback.message.edit_text("👤 لطفاً یک نام کاربری (انگلیسی) ارسال کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "rand_user", state=BotState.entering_username)
async def rand_user(callback: types.CallbackQuery, state: FSMContext):
    uname = ''.join(random.choices(string.ascii_lowercase, k=8))
    await state.update_data(username=uname)
    await show_final_invoice(callback.message, state)

@dp.message_handler(state=BotState.entering_username)
async def get_custom_user(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    await show_final_invoice(message, state)

async def show_final_invoice(message: types.Message, state: FSMContext):
    data = await state.get_data()
    inv_id = ''.join(random.choices(string.digits, k=8))
    await state.update_data(inv_id=inv_id)
    text = (f"🧾 فاکتور خرید اشتراک\n\n📦 سرویس: {data['p_name']}\n👤 یوزرنیم: {data['username']}\n💰 مبلغ: {int(data['p_price']):,.0f} تومان\n🆔 شناسه: {inv_id}")
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card"),
           types.InlineKeyboardButton("لغو", callback_data="back_to_main"))
    if message.from_user.id == bot.id: await message.edit_text(text, reply_markup=kb)
    else: await message.answer(text, reply_markup=kb)

# --- حساب کاربری ---
@dp.callback_query_handler(lambda c: c.data == "account", state="*")
async def account(callback: types.CallbackQuery):
    d, count = get_user_info(callback.from_user.id)
    text = (f"👤 شناسه کاربری:\n{callback.from_user.id}\n\n💰 موجودی: {d[0]:,.0f} تومان\n👥 زیرمجموعه: {count}\n📆 عضویت: {d[2]}")
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("افزایش موجودی", callback_data="add_balance"),
                                         types.InlineKeyboardButton("بازگشت", callback_data="back_to_main"))
    await callback.message.edit_text(text, reply_markup=kb)

# --- افزایش موجودی ---
@dp.callback_query_handler(lambda c: c.data == "add_balance", state="*")
async def start_charge(callback: types.CallbackQuery):
    await BotState.entering_amount.set()
    await callback.message.edit_text("💰 مبلغ شارژ را به تومان وارد کنید (70,000 تا 2,000,000):")

@dp.message_handler(state=BotState.entering_amount)
async def process_charge(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("فقط عدد!")
    amt = int(message.text)
    if 70000 <= amt <= 2000000:
        inv_id = f"CH{random.randint(100,999)}"
        await state.update_data(charge_amt=amt, inv_id=inv_id, off_applied=False)
        # فراخوانی تابع فاکتور شارژ (مشابه قبلی)
        text = f"🧾 فاکتور شارژ\n💰 مبلغ: {amt:,.0f}\n🆔 شناسه: {inv_id}"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("پرداخت", callback_data="pay_card"),
                                              types.InlineKeyboardButton("اعمال کد تخفیف", callback_data="apply_off"))
        await message.answer(text, reply_markup=kb)
    else: await message.answer("مبلغ خارج از محدوده!")

@dp.callback_query_handler(lambda c: c.data == "back_to_main", state="*")
async def back(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text("🌹 منوی اصلی:", reply_markup=main_menu_inline())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
