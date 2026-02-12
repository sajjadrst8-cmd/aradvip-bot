import logging
import sqlite3
import random
import string
import datetime
import re
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# --- تنظیمات اصلی (توکن و ایدی ادمین را اینجا بزنید) ---
API_TOKEN = 'توکن_ربات_شما'
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
        now = datetime.datetime.now().strftime("%Y/%m/%d - %H:%M")
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
    ref_id = message.get_args()
    get_user_info(user_id) 

    if ref_id and ref_id.isdigit() and int(ref_id) != user_id:
        conn = sqlite3.connect('arad_data.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET referred_by=? WHERE user_id=? AND referred_by IS NULL", (ref_id, user_id))
        if cursor.rowcount > 0:
            try: await bot.send_message(ref_id, f"🔔 کاربر {user_id} با کد دعوت شما وارد ربات شد")
            except: pass
        conn.commit()
        conn.close()
    await message.answer("🌹 به ربات آراد وی‌آی‌پی خوش آمدید!", reply_markup=main_menu_inline())

# --- منوی خرید ---
@dp.callback_query_handler(lambda c: c.data == "buy_menu", state="*")
async def buy_menu(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("🛰 V2ray (نیم بها + نامحدود)", callback_data="type_v2ray"),
           types.InlineKeyboardButton("🚀 Biubiu VPN", callback_data="type_biubiu"),
           types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
    await callback.message.edit_text("لطفا نوع سرویس را انتخاب کنید:", reply_markup=kb)

# --- تعرفه‌های V2ray (با چیدمان دقیق شما) ---
@dp.callback_query_handler(lambda c: c.data == "type_v2ray")
async def v2ray_plans(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    v2_list = [
        ("5گیگ زمان نامحدود 100 هزار تومان", "100000"),
        ("10گیگ زمان نامحدود 100 هزار تومان", "100000"),
        ("20گیگ زمان نامحدود 100 هزار تومان", "100000"),
        ("30گیگ زمان نامحدود 100 هزار تومان", "100000"),
        ("50گیگ زمان نامحدود 100 هزار تومان", "100000"),
        ("100گیگ زمان نامحدود 100 هزار تومان", "100000"),
        ("200گیگ زمان نامحدود 100 هزار تومان", "100000"),
        ("300گیگ زمان نامحدود 100 هزار تومان", "100000")
    ]
    for text, price in v2_list:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"set_buy_V2ray_{price}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_menu"))
    await callback.message.edit_text("🛰 لیست تعرفه‌های V2ray:", reply_markup=kb)

# --- تعرفه‌های Biubiu ---
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
        plans = [("1ماهه نامحدود (تک) - 100,000", "100000"), ("2ماهه (تک) - 200,000", "200000"), ("3ماهه (تک) - 300,000", "300000")]
    else:
        plans = [("1ماهه (دو) - 300,000", "300000"), ("3ماهه (دو) - 600,000", "600000"), ("6ماهه (دو) - 1,100,000", "1100000"), ("12ماهه (دو) - 1,800,000", "1800000")]
    for text, price in plans:
        kb.add(types.InlineKeyboardButton(f"{text} تومان", callback_data=f"set_buy_Biu_{price}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="type_biubiu"))
    await callback.message.edit_text("یک پلن را انتخاب کنید:", reply_markup=kb)

# --- فرآیند خرید و یوزرنیم ---
@dp.callback_query_handler(lambda c: c.data.startswith("set_buy_"), state="*")
async def ask_username(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    await state.update_data(p_type="BUY", p_name=data[2], p_price=data[-1], off_applied=False)
    await BotState.entering_username.set()
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🎲 نام کاربری تصادفی", callback_data="rand_user"))
    await callback.message.edit_text("👤 لطفاً یک نام کاربری (انگلیسی) ارسال کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "rand_user", state=BotState.entering_username)
async def rand_user(callback: types.CallbackQuery, state: FSMContext):
    uname = ''.join(random.choices(string.ascii_lowercase, k=8))
    await state.update_data(username=uname)
    await show_invoice(callback.message, state)

@dp.message_handler(state=BotState.entering_username)
async def get_custom_user(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    await show_invoice(message, state)

# --- حساب کاربری ---
@dp.callback_query_handler(lambda c: c.data == "account", state="*")
async def view_account(callback: types.CallbackQuery):
    data, ref_count = get_user_info(callback.from_user.id)
    text = (f"👤 شناسه کاربری:\n{callback.from_user.id}\n"
            f"🔐 وضعیت: 👤 کاربر عادی\n"
            f"💰 موجودی کیف پول: {data[0]:,.0f} تومان\n"
            f"👥 تعداد زیرمجموعه‌ها: {ref_count}\n\n"
            f"📆 تاریخ عضویت: {data[2]}")
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("افزایش موجودی", callback_data="add_balance"),
           types.InlineKeyboardButton("زیرمجموعه گیری", callback_data="ref_system"))
    kb.add(types.InlineKeyboardButton("بازگشت", callback_data="back_to_main"))
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "add_balance", state="*")
async def charge_start(callback: types.CallbackQuery):
    await BotState.entering_amount.set()
    await callback.message.edit_text("💰 مبلغ شارژ را به تومان وارد کنید (70,000 تا 2,000,000):")

@dp.message_handler(state=BotState.entering_amount)
async def charge_process(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ فقط عدد!")
    amt = int(message.text)
    if 70000 <= amt <= 2000000:
        inv_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        await state.update_data(p_type="CHARGE", charge_amt=amt, inv_id=inv_id, off_applied=False)
        await show_invoice(message, state)
    else: await message.answer("❌ مبلغ باید بین 70,000 تا 2,000,000 تومان باشد.")

# --- نمایش فاکتور (با اعمال منطق صحیح تخفیف) ---
async def show_invoice(message: types.Message, state: FSMContext):
    data = await state.get_data()
    is_charge = data['p_type'] == "CHARGE"
    amt = data['charge_amt'] if is_charge else int(data['p_price'])
    final = amt - (amt * (OFF_PERCENT/100)) if data['off_applied'] else amt
    inv_id = data.get('inv_id', 'INV'+str(random.randint(100,999)))
    
    text = (f"✅ فاکتور {'شارژ' if is_charge else 'خرید'} ایجاد شد.\n\n"
            f"🧾 شناسه: `{inv_id}`\n💰 مبلغ اصلی: {amt:,.0f} تومان\n"
            f"💸 مبلغ قابل پرداخت: {final:,.0f} تومان\n"
            f"👤 کاربر: {message.from_user.id if hasattr(message, 'from_user') else '-'}")
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("💳 پرداخت و ارسال رسید", callback_data="pay_now"),
           types.InlineKeyboardButton("🎟 اعمال کد تخفیف", callback_data="apply_off"),
           types.InlineKeyboardButton("❌ لغو", callback_data="back_to_main"))
    
    if message.from_user.id == bot.id: await message.edit_text(text, reply_markup=kb)
    else: await message.answer(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "apply_off", state="*")
async def off_prompt(callback: types.CallbackQuery):
    await BotState.entering_offcode.set()
    await callback.message.answer("🎟 کد تخفیف را وارد کنید:")

@dp.message_handler(state=BotState.entering_offcode)
async def off_check(message: types.Message, state: FSMContext):
    if message.text == ADMIN_OFF_CODE:
        await state.update_data(off_applied=True)
        await message.answer("✅ تخفیف اعمال شد.")
        await show_invoice(message, state)
    else: await message.answer("❌ کد نامعتبر.")

@dp.callback_query_handler(lambda c: c.data == "pay_now", state="*")
async def pay_info(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    is_charge = data['p_type'] == "CHARGE"
    amt = data['charge_amt'] if is_charge else int(data['p_price'])
    final = amt - (amt * (OFF_PERCENT/100)) if data['off_applied'] else amt
    await callback.message.edit_text(f"💳 شماره کارت: `{CARD_NUMBER}`\n👤 بنام: {CARD_NAME}\n💰 مبلغ: {final:,.0f} تومان\n\n📸 تصویر رسید را بفرستید:")
    await BotState.waiting_for_receipt.set()

# --- تایید/رد توسط ادمین (نسخه نهایی و اصلاح شده) ---
@dp.message_handler(content_types=['photo'], state=BotState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    p_type = data.get('p_type', 'CHARGE') 
    amt_to_pay = data.get('charge_amt') if p_type == "CHARGE" else int(data.get('p_price', 0))
    if data.get('off_applied'):
        amt_to_pay = amt_to_pay - (amt_to_pay * (OFF_PERCENT/100))
    
    # مبلغی که باید شارژ شود (مبلغ اصلی بدون کسر تخفیف)
    amt_to_add = data.get('charge_amt') if p_type == "CHARGE" else int(data.get('p_price', 0))
    
    await message.answer("✅ رسید برای ادمین ارسال شد.", reply_markup=main_menu_inline())
    
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✅ تایید و شارژ مبلغ اصلی", callback_data=f"adm_ok_{message.from_user.id}_{amt_to_add}_{p_type}"),
        types.InlineKeyboardButton("❌ رد رسید", callback_data=f"adm_no_{message.from_user.id}")
    )
    
    caption = (f"🔔 رسید جدید\n👤 کاربر: {message.from_user.id}\n"
               f"💰 واریزی (با تخفیف): {int(amt_to_pay):,.0f}\n"
               f"💎 شارژ حساب (اصلی): {int(amt_to_add):,.0f}\n"
               f"📂 نوع: {p_type}\n🔑 یوزر: {data.get('username', '-')}")
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=kb)
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith("adm_"), state="*")
async def admin_verify(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    action, user_id = parts[1], parts[2]
    
    if action == "ok":
        amount_full = float(parts[3])
        p_type = parts[4]
        if p_type == "CHARGE":
            conn = sqlite3.connect('arad_data.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET wallet = wallet + ? WHERE user_id=?", (amount_full, user_id))
            conn.commit()
            conn.close()
            await bot.send_message(user_id, f"✅ حساب شما مبلغ {amount_full:,.0f} تومان شارژ شد.")
        else:
            await bot.send_message(user_id, "✅ پرداخت شما تایید شد. سرویس به زودی ارسال می‌شود.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ تایید شد.")
    
    elif action == "no":
        await bot.send_message(user_id, "❌ رسید شما رد شد.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ رد شد.")
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "back_to_main", state="*")
async def back(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text("🌹 منوی اصلی:", reply_markup=main_menu_inline())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
