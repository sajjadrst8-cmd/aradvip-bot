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
OFF_CODE = "ARAD20" # کد تخفیف نمونه (قابل تغییر توسط شما در کد)
OFF_PERCENT = 20    # درصد تخفیف

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
    entering_amount = State() # مبلغ شارژ
    entering_offcode = State() # کد تخفیف
    entering_username = State()
    waiting_for_receipt = State()

# --- توابع کمکی ---
def get_user_data(user_id):
    conn = sqlite3.connect('arad_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT wallet, referred_by, join_date FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    if not data:
        now = datetime.now().strftime("%Y/%m/%d")
        cursor.execute("INSERT INTO users (user_id, wallet, join_date) VALUES (?, 0, ?)", (user_id, now))
        conn.commit()
        data = (0, None, now)
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (user_id,))
    ref_count = cursor.fetchone()[0]
    conn.close()
    return data, ref_count

# --- منوی اصلی ---
def main_menu_inline():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(types.InlineKeyboardButton("🛍 خرید اشتراک جدید", callback_data="buy_menu"),
                 types.InlineKeyboardButton("🎁 دریافت اشتراک تست", callback_data="get_test"))
    keyboard.add(types.InlineKeyboardButton("📜 اشتراک‌های من", callback_data="my_subs"),
                 types.InlineKeyboardButton("🧾 فاکتورهای من", callback_data="my_invoices"))
    keyboard.add(types.InlineKeyboardButton("👤 حساب کاربری", callback_data="account"))
    keyboard.add(types.InlineKeyboardButton("📞 پشتیبانی", callback_data="support"),
                 types.InlineKeyboardButton("📚 آموزش اتصال", callback_data="tutorial"))
    keyboard.add(types.InlineKeyboardButton("📊 وضعیت سرویس‌ها", callback_data="status"))
    return keyboard

# --- هندلر استارت (با سیستم زیرمجموعه‌گیری) ---
@dp.message_handler(commands=['start'], state="*")
async def send_welcome(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    ref_id = message.get_args() # گرفتن آیدی دعوت از لینک
    
    conn = sqlite3.connect('arad_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        now = datetime.now().strftime("%Y/%m/%d")
        ref_val = int(ref_id) if ref_id and ref_id.isdigit() else None
        cursor.execute("INSERT INTO users (user_id, wallet, referred_by, join_date) VALUES (?, 0, ?, ?)", 
                       (user_id, ref_val, now))
        conn.commit()
        if ref_val:
            try:
                await bot.send_message(ref_val, f"🔔 کاربر `{user_id}` با کد دعوت شما وارد ربات شد!", parse_mode="Markdown")
            except: pass
    conn.close()
    await message.answer("🌹 به ربat آراد خوش آمدید!", reply_markup=main_menu_inline())

# --- بخش حساب کاربری ---
@dp.callback_query_handler(lambda c: c.data == "account", state="*")
async def account_menu(callback: types.CallbackQuery):
    u_data, ref_count = get_user_data(callback.from_user.id)
    wallet, _, j_date = u_data
    
    text = (f"👤 **حساب کاربری شما**\n\n"
            f"🆔 شناسه کاربری: `{callback.from_user.id}`\n"
            f"🔐 وضعیت: 👤 کاربر عادی\n"
            f"💰 موجودی کیف پول: {wallet:,.0f} تومان\n"
            f"👥 تعداد زیرمجموعه‌ها: {ref_count}\n"
            f"📆 تاریخ عضویت: {j_date}")
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("➕ افزایش موجودی", callback_data="add_balance"),
           types.InlineKeyboardButton("👥 زیرمجموعه گیری", callback_data="ref_system"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
    
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- زیرمجموعه‌گیری ---
@dp.callback_query_handler(lambda c: c.data == "ref_system")
async def ref_info(callback: types.CallbackQuery):
    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={callback.from_user.id}"
    
    text = (f"👥 **سیستم کسب درآمد**\n\n"
            f"🔗 لینک اختصاصی شما:\n`{ref_link}`\n\n"
            f"🎁 دوستان خود را دعوت کنید و 10% از مبلغ خرید آنها را هدیه بگیرید!")
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 بازگشت به حساب", callback_data="account"))
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- افزایش موجودی ---
@dp.callback_query_handler(lambda c: c.data == "add_balance")
async def ask_amount(callback: types.CallbackQuery):
    await BotState.entering_amount.set()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="account"))
    await callback.message.edit_text("💰 لطفاً مبلغ مورد نظر خود را به **تومان** وارد کنید:\n\n"
                                     "⚠️ حداقل: 70,000 تومان\n"
                                     "⚠️ حداکثر: 2,000,000 تومان", reply_markup=kb, parse_mode="Markdown")

@dp.message_handler(state=BotState.entering_amount)
async def process_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❌ لطفا فقط عدد وارد کنید!")
    
    amount = int(message.text)
    if amount < 70000 or amount > 2000000:
        return await message.answer("❌ مبلغ باید بین 70,000 تا 2,000,000 تومان باشد.")
    
    inv_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    await state.update_data(charge_amount=amount, current_inv=inv_id, off_applied=0)
    
    await show_charge_invoice(message, state)

async def show_charge_invoice(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = data['charge_amount']
    off_price = amount - (amount * OFF_PERCENT / 100) if data.get('off_applied') else amount
    
    text = (f"✅ فاکتور افزایش موجودی ایجاد شد.\n\n"
            f"🧾 شناسه: `{data['current_inv']}`\n"
            f"🟠 وضعیت: در انتظار\n"
            f"💰 مبلغ: {amount:,.0f} تومان\n"
            f"💸 پس از تخفیف: {f'{off_price:,.0f} تومان' if data.get('off_applied') else '-'}\n"
            f"📦 نوع: 💰 شارژ کیف پول\n"
            f"👤 کاربر: {message.from_user.id}")
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("💳 پرداخت فاکتور (کارت به کارت)", callback_data="pay_charge"),
           types.InlineKeyboardButton("🎟 اعمال کد تخفیف", callback_data="apply_off"),
           types.InlineKeyboardButton("❌ لغو فاکتور", callback_data="back_to_main"))
    
    if message.from_user.id == bot.id:
        await message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")

# --- کد تخفیف ---
@dp.callback_query_handler(lambda c: c.data == "apply_off", state="*")
async def off_start(callback: types.CallbackQuery):
    await BotState.entering_offcode.set()
    await callback.message.answer("🎟 لطفا کد تخفیف خود را وارد کنید:")

@dp.message_handler(state=BotState.entering_offcode)
async def check_off(message: types.Message, state: FSMContext):
    if message.text == OFF_CODE:
        await state.update_data(off_applied=True)
        await message.answer(f"✅ کد تخفیف اعمال شد! {OFF_PERCENT}% کسر گردید.")
        await show_charge_invoice(message, state)
    else:
        await message.answer("❌ کد تخفیف نامعتبر است.")

# --- پرداخت شارژ و رسید ---
@dp.callback_query_handler(lambda c: c.data == "pay_charge", state="*")
async def pay_charge_info(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data['charge_amount']
    final_price = amount - (amount * OFF_PERCENT / 100) if data.get('off_applied') else amount
    
    text = (f"💳 اطلاعات کارت جهت شارژ:\n\n"
            f"شماره کارت: `{CARD_NUMBER}`\n"
            f"به نام: {CARD_NAME}\n"
            f"💰 مبلغ نهایی: {final_price:,.0f} تومان\n\n"
            "📸 لطفا عکس رسید را ارسال کنید:")
    await callback.message.edit_text(text, parse_mode="Markdown")
    await BotState.waiting_for_receipt.set()

# --- تایید ادمین و افزایش موجودی واقعی ---
@dp.callback_query_handler(lambda c: c.data.startswith("adm_"), state="*")
async def admin_decision(callback: types.CallbackQuery):
    _, action, uid, inv = callback.data.split("_")
    
    if action == "ok":
        # در اینجا ادمین تایید میکند و موجودی کاربر در دیتابیس اضافه میشود
        conn = sqlite3.connect('arad_data.db')
        cursor = conn.cursor()
        # فرض میکنیم مبلغ شارژ را از جایی میخوانیم، اینجا برای سادگی در مسیج ادمین بوده
        # ادمین مبلغ نهایی را تایید میکند
        cursor.execute("UPDATE users SET wallet = wallet + (SELECT 100000) WHERE user_id=?", (uid,)) # مبلغ نمونه
        conn.commit()
        conn.close()
        
        await bot.send_message(uid, f"✅ فاکتور {inv} تایید شد و موجودی حساب شما شارژ گردید!")
    else:
        await bot.send_message(uid, f"❌ رسید شما رد شد.")
    await callback.message.edit_caption("تکمیل شد.")
