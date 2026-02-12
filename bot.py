import logging
import sqlite3
import random
import string
import datetime
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# --- تنظیمات اصلی ---
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

@dp.callback_query_handler(lambda c: c.data == "type_biubiu")
async def biubiu_select(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("👤 تک کاربره", callback_data="biu_single"),
           types.InlineKeyboardButton("👥 دو کاربره", callback_data="biu_double"),
           types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_menu"))
    await callback.message.edit_text("نوع اشتراک Biubiu را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "type_v2ray")
async def v2ray_plans(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    # لیست کامل حجم‌های V2ray
    v2_plans = [
        ("5 گیگ بدون محدودیت کاربر 50 هزار تومن"),
        ("V2ray 10 گیگ (زمان نامحدود)", "80000"),
        ("V2ray 20 گیگ (زمان نامحدود)", "120000"),
        ("V2ray 30 گیگ (زمان نامحدود)", "150000"),
        ("V2ray 50 گیگ (زمان نامحدود)", "200000"),
        ("V2ray 100 گیگ (زمان نامحدود)", "350000")
    ]
    for text, price in v2_plans:
        kb.add(types.InlineKeyboardButton(f"{text} - {int(price):,.0f} تومان", callback_data=f"set_buy_V2ray_{price}"))
    
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_menu"))
    await callback.message.edit_text("🛰 پلن‌های V2ray (نیم‌بها + اختصاصی) را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("biu_"))
async def biubiu_plans(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    # تعرفه‌های دقیق شما
    if "single" in callback.data:
        plans = [("1ماهه نامحدود (تک) - 100,000", "100000"), ("2ماهه (تک) - 200,000", "200000"), ("3ماهه (تک) - 300,000", "300000")]
    else:
        plans = [("1ماهه (دو) - 300,000", "300000"), ("3ماهه (دو) - 600,000", "600000"), ("6ماهه (دو) - 1,100,000", "1100000"), ("12ماهه (دو) - 1,800,000", "1800000")]
    for text, price in plans:
        kb.add(types.InlineKeyboardButton(f"{text} تومان", callback_data=f"set_buy_Biu_{price}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="type_biubiu"))
    await callback.message.edit_text("یک پلن را انتخاب کنید:", reply_markup=kb)

# --- فرآیند خرید: درخواست یوزرنیم ---
@dp.callback_query_handler(lambda c: c.data.startswith("set_buy_"), state="*")
async def ask_username(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    await state.update_data(p_type="BUY", p_name=data[2], p_price=data[-1], off_applied=False)
    await BotState.entering_username.set()
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🎲 نام کاربری تصادفی", callback_data="rand_user"))
    await callback.message.edit_text("👤 لطفاً یک نام کاربری (انگلیسی) برای اشتراک ارسال کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "rand_user", state=BotState.entering_username)
async def rand_user(callback: types.CallbackQuery, state: FSMContext):
    uname = ''.join(random.choices(string.ascii_lowercase, k=8))
    await state.update_data(username=uname)
    await show_invoice(callback.message, state)

@dp.message_handler(state=BotState.entering_username)
async def get_custom_user(message: types.Message, state: FSMContext):
    if not re.match("^[A-Za-z0-9_]*$", message.text):
        return await message.answer("❌ نام کاربری فقط باید شامل حروف انگلیسی و عدد باشد.")
    await state.update_data(username=message.text)
    await show_invoice(message, state)

# --- حساب کاربری (فرمت دقیق درخواستی) ---
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

# --- افزایش موجودی ---
@dp.callback_query_handler(lambda c: c.data == "add_balance", state="*")
async def charge_start(callback: types.CallbackQuery):
    await BotState.entering_amount.set()
    await callback.message.edit_text("💰 لطفاً مبلغ شارژ را به تومن وارد کنید (70,000 تا 2,000,000):")

@dp.message_handler(state=BotState.entering_amount)
async def charge_process(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("❌ فقط عدد!")
    amt = int(message.text)
    if 70000 <= amt <= 2000000:
        inv_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        await state.update_data(p_type="CHARGE", charge_amt=amt, inv_id=inv_id, off_applied=False)
        await show_invoice(message, state)
    else: await message.answer("❌ مبلغ باید بین 70,000 تا 2,000,000 تومان باشد.")

# --- نمایش فاکتور مشترک (شارژ و خرید) ---
async def show_invoice(message: types.Message, state: FSMContext):
    data = await state.get_data()
    is_charge = data['p_type'] == "CHARGE"
    amt = data['charge_amt'] if is_charge else int(data['p_price'])
    final = amt - (amt * (OFF_PERCENT/100)) if data['off_applied'] else amt
    inv_id = data.get('inv_id', 'INV'+str(random.randint(100,999)))
    
    text = (f"✅ فاکتور {'شارژ کیف پول' if is_charge else 'خرید اشتراک'} ایجاد شد.\n\n"
            f"🧾 شناسه: `{inv_id}`\n📌 وضعیت: 🟠 در انتظار\n"
            f"💰 مبلغ: {amt:,.0f} تومان\n"
            f"💸 پس از تخفیف: {f'{final:,.0f} تومان' if data['off_applied'] else '- تومان'}\n"
            f"📦 نوع: {'💰 شارژ' if is_charge else '🚀 اشتراک'}\n"
            f"👤 کاربر: {message.from_user.id if hasattr(message, 'from_user') else '-'}")
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_via_card"),
           types.InlineKeyboardButton("🎟 اعمال کد تخفیف", callback_data="apply_off"),
           types.InlineKeyboardButton("❌ لغو فاکتور", callback_data="back_to_main"))
    
    if message.from_user.id == bot.id: await message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    else: await message.answer(text, reply_markup=kb, parse_mode="Markdown")

# --- کد تخفیف ---
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
    else: await message.answer("❌ کد نامعتبر است.")

# --- پرداخت و ارسال رسید ---
@dp.callback_query_handler(lambda c: c.data == "pay_via_card", state="*")
async def pay_info(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    is_charge = data['p_type'] == "CHARGE"
    amt = data['charge_amt'] if is_charge else int(data['p_price'])
    final = amt - (amt * (OFF_PERCENT/100)) if data['off_applied'] else amt
    
    text = (f"💳 شماره کارت: `{CARD_NUMBER}`\n👤 بنام: {CARD_NAME}\n"
            f"💰 مبلغ قابل پرداخت: {final:,.0f} تومان\n\n"
            "📸 لطفاً تصویر رسید واریز را ارسال کنید:")
    await callback.message.edit_text(text, parse_mode="Markdown")
    await BotState.waiting_for_receipt.set()

@dp.message_handler(content_types=['photo'], state=BotState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    is_charge = data['p_type'] == "CHARGE"
    amt = data['charge_amt'] if is_charge else int(data['p_price'])
    final = amt - (amt * (OFF_PERCENT/100)) if data['off_applied'] else amt
    
    await message.answer("✅ رسید برای ادمین ارسال شد. منتظر تایید باشید.", reply_markup=main_menu_inline())
    
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✅ تایید", callback_data=f"adm_ok_{message.from_user.id}_{final}_{data['p_type']}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"adm_no_{message.from_user.id}")
    )
    
    caption = (f"🔔 رسید جدید\n👤 کاربر: {message.from_user.id}\n"
               f"💰 مبلغ: {final:,.0f}\n📂 نوع: {data['p_type']}\n"
               f"🔑 یوزرنیم درخواستی: {data.get('username', '-')}")
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=kb)
    await state.finish()

# --- تایید نهایی توسط ادمین ---
@dp.callback_query_handler(lambda c: c.data.startswith("adm_"), state="*")
async def admin_verify(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    action, user_id, amount, p_type = parts[1], parts[2], parts[3], parts[4] if len(parts)>4 else "CHARGE"
    
    if action == "ok":
        if p_type == "CHARGE":
            conn = sqlite3.connect('arad_data.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET wallet = wallet + ? WHERE user_id=?", (float(amount), user_id))
            conn.commit()
            conn.close()
            await bot.send_message(user_id, f"✅ فاکتور شما تایید شد و مبلغ {float(amount):,.0f} تومان به کیف پول شما اضافه شد.")
        else:
            await bot.send_message(user_id, f"✅ پرداخت شما تایید شد. اشتراک شما تا دقایقی دیگر ارسال می‌شود.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ تایید گردید.")
    else:
        await bot.send_message(user_id, "❌ متاسفانه رسید ارسالی شما رد شد. لطفاً با پشتیبانی در ارتباط باشید.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ رد شد.")

@dp.callback_query_handler(lambda c: c.data == "back_to_main", state="*")
async def back_main(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text("🌹 منوی اصلی:", reply_markup=main_menu_inline())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
