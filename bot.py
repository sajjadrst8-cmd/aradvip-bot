import asyncio
import logging
import sqlite3
import random
import string
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.deep_linking import create_start_link

# ================= تنظیمات =================
API_TOKEN = '8584319269:AAGFrJ0jXy5SHktP-VQE2jjUBVnW65fLcdw' 
ADMIN_ID = 863961919  # آیدی عددی خودتان
CARD_NUMBER = "5057851560122222"
CARD_NAME = "سجاد رستگاران"
REF_BONUS = 5000  # هدیه زیرمجموعه‌گیری به تومان

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ================= دیتابیس =================
conn = sqlite3.connect('v2ray_pro.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, 
                   test_usage INTEGER DEFAULT 0, joined_date TEXT, inviter_id INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS invoices 
                  (id TEXT PRIMARY KEY, user_id INTEGER, amount INTEGER, 
                   status TEXT, date TEXT, plan_name TEXT, alias TEXT)''')
conn.commit()

class BotStates(StatesGroup):
    entering_username = State()
    sending_receipt = State()

# ================= منوها =================
def get_main_menu():
    kb = [
        [KeyboardButton(text="خرید اشتراک جدید"), KeyboardButton(text="دریافت اشتراک تست")],
        [KeyboardButton(text="حساب کاربری"), KeyboardButton(text="زیرمجموعه گیری")],
        [KeyboardButton(text="پشتیبانی / آموزش اتصال")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# ================= هندلرها =================

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    uid = message.from_user.id
    # بررسی زیرمجموعه
    args = message.text.split()
    inviter = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, balance, test_usage, joined_date, inviter_id) VALUES (?, 0, 0, ?, ?)", 
                       (uid, datetime.now().strftime("%Y/%m/%d"), inviter))
        conn.commit()
        if inviter:
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (REF_BONUS, inviter))
            conn.commit()
            try:
                await bot.send_message(inviter, f"🎉 یک نفر با لینک شما عضو شد! مبلغ {REF_BONUS:,} تومان به کیف پول شما اضافه شد.")
            except: pass
            
    await message.answer(f"سلام {message.from_user.first_name} خوش آمدید!", reply_markup=get_main_menu())

@dp.message(F.text == "زیرمجموعه گیری")
async def referral_menu(message: types.Message):
    uid = message.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={uid}"
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE inviter_id = ?", (uid,))
    count = cursor.fetchone()[0]
    
    text = (f"👥 <b>سیستم زیرمجموعه‌گیری</b>\n\n"
            f"با دعوت دوستان خود، مبلغ {REF_BONUS:,} تومان اعتبار هدیه بگیرید.\n\n"
            f"📈 تعداد افراد دعوت شده: {count} نفر\n"
            f"🔗 لینک اختصاصی شما:\n<code>{ref_link}</code>")
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "حساب کاربری")
async def account_info(message: types.Message):
    uid = message.from_user.id
    cursor.execute("SELECT balance, joined_date FROM users WHERE user_id=?", (uid,))
    user = cursor.fetchone()
    
    cursor.execute("SELECT plan_name, status FROM invoices WHERE user_id=? ORDER BY date DESC LIMIT 3", (uid,))
    purchases = cursor.fetchall()
    history = "\n".join([f"🔹 {p[0]} | {p[1]}" for p in purchases]) if purchases else "سابقه‌ای ندارد."

    text = (f"👤 <b>اطلاعات حساب:</b>\n\n"
            f"💰 موجودی: {user[0]:,} تومان\n"
            f"📅 تاریخ عضویت: {user[1]}\n\n"
            f"📦 آخرین خریدها:\n{history}")
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "خرید اشتراک جدید")
async def buy_menu(message: types.Message):
    kb = [
        [KeyboardButton(text="V2ray 10GB (100,000 تومان)")],
        [KeyboardButton(text="V2ray 20GB (180,000 تومان)")],
        [KeyboardButton(text="بازگشت")]
    ]
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("یکی از پلن‌ها را انتخاب کنید:", reply_markup=markup)

@dp.message(F.text.contains("تومان"))
async def ask_username(message: types.Message, state: FSMContext):
    # استخراج قیمت از متن
    price = int(''.join(filter(str.isdigit, message.text.replace(',', ''))))
    await state.update_data(plan=message.text, price=price)
    await message.answer("👤 یک نام کاربری (انگلیسی) برای اشتراک خود بفرستید:")
    await state.set_state(BotStates.entering_username)

@dp.message(BotStates.entering_username)
async def process_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    inv_id = "".join(random.choices(string.digits, k=6))
    cursor.execute("INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (inv_id, message.from_user.id, data['price'], "⏳ در انتظار پرداخت", 
                    datetime.now().strftime("%Y/%m/%d"), data['plan'], message.text))
    conn.commit()
    
    builder = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 پرداخت و ارسال رسید", callback_data=f"pay_{inv_id}")]
    ])
    await message.answer(f"📑 فاکتور {inv_id} صادر شد.\n💰 مبلغ: {data['price']:,} تومان", reply_markup=builder)
    await state.clear()

@dp.callback_query(F.data.startswith("pay_"))
async def pay_step(callback: types.CallbackQuery, state: FSMContext):
    inv_id = callback.data.split('_')[1]
    await state.update_data(curr_inv=inv_id)
    await callback.message.answer(f"💳 کارت: `{CARD_NUMBER}`\n👤 بنام: {CARD_NAME}\n\n✅ پس از واریز، عکس رسید را بفرستید.")
    await state.set_state(BotStates.sending_receipt)

@dp.message(BotStates.sending_receipt, F.photo)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    builder = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تایید", callback_data=f"ok_{data['curr_inv']}"),
         InlineKeyboardButton(text="❌ رد", callback_data=f"no_{data['curr_inv']}")]
    ])
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"💰 رسید جدید!\nکاربر: {message.from_user.id}\nفاکتور: {data['curr_inv']}", 
                         reply_markup=builder)
    await message.answer("⏳ رسید برای مدیریت ارسال شد. لطفاً منتظر تایید بمانید.")
    await state.clear()

@dp.callback_query(F.data.startswith("ok_") | F.data.startswith("no_"))
async def admin_decision(callback: types.CallbackQuery):
    action, inv_id = callback.data.split('_')
    cursor.execute("SELECT user_id, plan_name FROM invoices WHERE id=?", (inv_id,))
    res = cursor.fetchone()
    if not res: return
    
    if action == "ok":
        cursor.execute("UPDATE invoices SET status = '✅ تایید شده' WHERE id = ?", (inv_id,))
        await bot.send_message(res[0], f"✅ پرداخت شما تایید شد!\n📦 سرویس {res[1]} برای شما فعال شد.")
    else:
        cursor.execute("UPDATE invoices SET status = '❌ رد شده' WHERE id = ?", (inv_id,))
        await bot.send_message(res[0], "❌ رسید شما توسط مدیریت رد شد.")
    conn.commit()
    await callback.message.edit_reply_markup(reply_markup=None)

@dp.message(F.text == "بازگشت")
async def back_cmd(message: types.Message):
    await start_cmd(message)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
