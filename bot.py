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
ADMIN_OFF_CODE = "ARAD2026" # کد تخفیف تعریف شده توسط ادمین
OFF_PERCENT = 20 # درصد تخفیف

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
    get_user_info(user_id) # ثبت کاربر

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

# --- حساب کاربری ---
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

# --- زیرمجموعه‌گیری ---
@dp.callback_query_handler(lambda c: c.data == "ref_system")
async def ref_page(callback: types.CallbackQuery):
    bot_name = (await bot.get_me()).username
    link = f"https://t.me/{bot_name}?start={callback.from_user.id}"
    text = (f"🔗 لینک دعوت شما:\n`{link}`\n\n"
            f"دوستان خودتونو به ربات دعوت کنید و 10 درصد از مبلغ خریدشونو دریافت کنید")
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("بازگشت", callback_data="account"))
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- افزایش موجودی ---
@dp.callback_query_handler(lambda c: c.data == "add_balance")
async def charge_start(callback: types.CallbackQuery):
    await BotState.entering_amount.set()
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("بازگشت", callback_data="account"))
    await callback.message.edit_text("لطفا مبلغ مورد نظر خودتون رو به تومن وارد کنید\n"
                                     "حداقل مبلغ شارژ 70000 تومن و حداکثر 2000000 تومان می‌باشد", reply_markup=kb)

@dp.message_handler(state=BotState.entering_amount)
async def charge_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❌ لطفا فقط عدد وارد کنید")
    
    amount = int(message.text)
    if amount < 70000 or amount > 2000000:
        return await message.answer("❌ مبلغ باید بین 70,000 تا 2,000,000 تومان باشد")
    
    inv_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
    await state.update_data(charge_amt=amount, inv_id=inv_id, off_applied=False)
    await show_charge_invoice(message, state)

async def show_charge_invoice(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amt = data['charge_amt']
    off_amt = amt * (OFF_PERCENT/100) if data['off_applied'] else 0
    final = amt - off_amt
    
    text = (f"✅ فاکتور افزایش موجودی ایجاد شد. برای پرداخت و مشاهده جزئیات روی دکمه زیر بزنید.\n\n"
            f"🧾 شناسه: `{data['inv_id']}`\n📌 وضعیت: 🟠 در انتظار\n💰 مبلغ: {amt:,.0f} تومان\n"
            f"💸 پس از تخفیف: {f'{final:,.0f} تومان' if data['off_applied'] else '- تومان'}\n"
            f"📦 نوع: 💰 شارژ کیف پول\n📆 تاریخ ثبت: {datetime.now().strftime('%Y/%m/%d - %H:%M')}\n"
            f"👤 کاربر: {message.from_user.id if hasattr(message, 'from_user') else '-'}")
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("پرداخت فاکتور", callback_data="pay_charge_now"),
           types.InlineKeyboardButton("اعمال کد تخفیف", callback_data="use_off_code"),
           types.InlineKeyboardButton("لغو فاکتور", callback_data="back_to_main"),
           types.InlineKeyboardButton("بازگشت", callback_data="account"))
    
    if message.from_user.id == bot.id: await message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    else: await message.answer(text, reply_markup=kb, parse_mode="Markdown")

# --- کد تخفیف ---
@dp.callback_query_handler(lambda c: c.data == "use_off_code", state="*")
async def off_input(callback: types.CallbackQuery):
    await BotState.entering_offcode.set()
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("بازگشت", callback_data="account"))
    await callback.message.answer("لطفا کد تخفیف خود را وارد کنید", reply_markup=kb)

@dp.message_handler(state=BotState.entering_offcode)
async def off_check(message: types.Message, state: FSMContext):
    if message.text == ADMIN_OFF_CODE:
        await state.update_data(off_applied=True)
        await message.answer("✅ کد تخفیف اعمال شد")
        await show_charge_invoice(message, state)
    else:
        await message.answer("❌ کد تخفیف معتبر نیست", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("بازگشت", callback_data="account")))

# --- پرداخت و ادمین ---
@dp.callback_query_handler(lambda c: c.data == "pay_charge_now", state="*")
async def pay_charge_card(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amt = data['charge_amt']
    final = amt - (amt * (OFF_PERCENT/100)) if data['off_applied'] else amt
    text = (f"💳 شماره کارت: `{CARD_NUMBER}`\n👤 بنام: {CARD_NAME}\n💰 مبلغ: {final:,.0f} تومان\n\n"
            "لطفاً پس از واریز، عکس رسید را اینجا بفرستید.")
    await callback.message.edit_text(text, parse_mode="Markdown")
    await BotState.waiting_for_receipt.set()

@dp.message_handler(content_types=['photo'], state=BotState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    inv = data.get('inv_id', 'شارژ مستقیم')
    amt = data.get('charge_amt', 0)
    final = amt - (amt * (OFF_PERCENT/100)) if data.get('off_applied') else amt

    await message.answer("✅ رسید دریافت شد و برای ادمین ارسال گردید. منتظر تایید بمانید.", reply_markup=main_menu_inline())
    
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✅ تایید", callback_data=f"confirm_ch_{message.from_user.id}_{final}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"decline_ch_{message.from_user.id}")
    )
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"🔔 درخواست شارژ\n👤 کاربر: {message.from_user.id}\n💰 مبلغ: {final:,.0f}\n🧾 فاکتور: {inv}", reply_markup=kb)
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith(('confirm_ch_', 'decline_ch_')), state="*")
async def admin_verify(callback: types.CallbackQuery):
    parts = callback.data.split('_')
    user_id = parts[2]
    
    if parts[0] == "confirm":
        amount = float(parts[3])
        conn = sqlite3.connect('arad_data.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET wallet = wallet + ? WHERE user_id=?", (amount, user_id))
        conn.commit()
        conn.close()
        await bot.send_message(user_id, f"✅ حساب شما مبلغ {amount:,.0f} تومان شارژ شد.")
        await callback.message.edit_caption("✅ تایید و شارژ شد")
    else:
        await bot.send_message(user_id, "❌ رسید شما توسط ادمین رد شد.")
        await callback.message.edit_caption("❌ رد شد")
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "back_to_main", state="*")
async def back_main(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text("🌹 منوی اصلی:", reply_markup=main_menu_inline())

# --- دکمه‌های خرید قبلی (Biubiu و V2ray) را هم به همین منوال به خرید اضافه کنید ---

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
