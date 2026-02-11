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
        cursor.execute("INSERT INTO users (user_id, wallet, join_date) VALUES (?, 0, ?)", (user_id, 0, now))
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

# --- شروع و زیرمجموعه‌گیری ---
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
            try: await bot.send_message(ref_id, f"کاربر {user_id} با کد دعوت شما وارد ربات شد")
            except: pass
        conn.commit()
        conn.close()
    await message.answer("🌹 به ربات آراد وی‌آی‌پی خوش آمدید!", reply_markup=main_menu_inline())

# --- منوی خرید و نمایش تعرفه‌ها (اصلاح شده) ---
@dp.callback_query_handler(lambda c: c.data == "buy_menu", state="*")
async def buy_menu_types(callback: types.CallbackQuery):
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
async def biubiu_plans_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    if "single" in callback.data:
        plans = [("1ماهه نامحدود (تک) - 100,000", "100000"), ("2ماهه نامحدود (تک) - 200,000", "200000"), ("3ماهه نامحدود (تک) - 300,000", "300000")]
    else:
        plans = [("1ماهه نامحدود (دو) - 300,000", "300000"), ("3ماهه نامحدود (دو) - 600,000", "600000"), ("6ماهه نامحدود (دو) - 1,100,000", "1100000"), ("12ماهه نامحدود (دو) - 1,800,000", "1800000")]
    for text, price in plans:
        kb.add(types.InlineKeyboardButton(f"{text} تومان", callback_data=f"set_plan_Biu_{price}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="type_biubiu"))
    await callback.message.edit_text("یک پلن را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "type_v2ray")
async def v2ray_plans_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    v2_plans = ["5گیگ", "10گیگ", "20گیگ", "30گیگ", "50گیگ", "100گیگ"]
    for p in v2_plans:
        kb.add(types.InlineKeyboardButton(f"{p} زمان نامحدود - 100,000 تومان", callback_data=f"set_plan_V2ray_{p}_100000"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_menu"))
    await callback.message.edit_text("پلن V2ray را انتخاب کنید:", reply_markup=kb)

# --- حساب کاربری و زیرمجموعه ---
@dp.callback_query_handler(lambda c: c.data == "account", state="*")
async def view_account(callback: types.CallbackQuery):
    data, ref_count = get_user_info(callback.from_user.id)
    wallet, _, join_date = data
    text = (f"👤 شناسه کاربری:\n{callback.from_user.id}\n\n"
            f"🔐 وضعیت: 👤 کاربر عادی\n"
            f"💰 موجودی کیف پول: {wallet:,.0f} تومان\n"
            f"👥 تعداد زیرمجموعه‌ها: {ref_count}\n\n"
            f"📆 تاریخ عضویت: {join_date}")
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("افزایش موجودی", callback_data="add_balance"),
           types.InlineKeyboardButton("زیرمجموعه گیری", callback_data="ref_system"))
    kb.add(types.InlineKeyboardButton("بازگشت", callback_data="back_to_main"))
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "ref_system")
async def ref_page(callback: types.CallbackQuery):
    bot_name = (await bot.get_me()).username
    link = f"https://t.me/{bot_name}?start={callback.from_user.id}"
    text = (f"🔗 لینک دعوت شما:\n`{link}`\n\n"
            f"دوستان خودتونو به ربات دعوت کنید و 10 درصد از مبلغ خریدشونو دریافت کنید")
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("بازگشت", callback_data="account"))
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- افزایش موجودی و فاکتور ---
@dp.callback_query_handler(lambda c: c.data == "add_balance")
async def charge_start(callback: types.CallbackQuery):
    await BotState.entering_amount.set()
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("بازگشت", callback_data="account"))
    await callback.message.edit_text("لطفا مبلغ مورد نظر خودتون رو به تومن وارد کنید\n"
                                     "حداقل مبلغ شارژ 70000 تومن و حداکثر 2000000 تومان می‌باشد", reply_markup=kb)

@dp.message_handler(state=BotState.entering_amount)
async def charge_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ فقط عدد وارد کنید")
    amount = int(message.text)
    if amount < 70000 or amount > 2000000: return await message.answer("❌ مبلغ نامعتبر است (بین 70هزار تا 2میلیون)")
    inv_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))
    await state.update_data(charge_amt=amount, inv_id=inv_id, off_applied=False)
    await show_charge_invoice(message, state)

async def show_charge_invoice(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amt = data['charge_amt']
    final = amt - (amt * (OFF_PERCENT/100)) if data['off_applied'] else amt
    text = (f"✅ فاکتور افزایش موجودی ایجاد شد.\n\n🧾 شناسه: `{data['inv_id']}`\n📌 وضعیت: 🟠 در انتظار\n💰 مبلغ: {amt:,.0f} تومان\n"
            f"💸 پس از تخفیف: {f'{final:,.0f} تومان' if data['off_applied'] else '- تومان'}\n📦 نوع: 💰 شارژ کیف پول\n"
            f"📆 تاریخ ثبت: {datetime.now().strftime('%Y/%m/%d - %H:%M')}\n👤 کاربر: {message.from_user.id if hasattr(message, 'from_user') else '-'}")
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("پرداخت فاکتور", callback_data="pay_charge_now"),
           types.InlineKeyboardButton("اعمال کد تخفیف", callback_data="use_off_code"),
           types.InlineKeyboardButton("لغو فاکتور", callback_data="back_to_main"),
           types.InlineKeyboardButton("بازگشت", callback_data="account"))
    if message.from_user.id == bot.id: await message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    else: await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data == "back_to_main", state="*")
async def back_main(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text("🌹 منوی اصلی:", reply_markup=main_menu_inline())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
