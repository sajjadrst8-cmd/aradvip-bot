import logging
import sqlite3
import random
import string
import re
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# --- تنظیمات ---
API_TOKEN = '8584319269:AAHT2fLxyC303MCl-jndJVSO7F27YO0hIAA'
ADMIN_ID = 863961919  
CARD_NUMBER = "5057851560122222"
CARD_NAME = "سجاد رستگاران"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class BuyState(StatesGroup):
    choosing_plan = State()
    entering_username = State()
    waiting_for_receipt = State()

# --- منوی اصلی کاملاً اینلاین ---
def main_menu_inline():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🛍 خرید اشتراک جدید", callback_data="buy_menu"),
        types.InlineKeyboardButton("🎁 دریافت اشتراک تست", callback_data="get_test")
    )
    # جدا کردن اشتراک‌ها و فاکتورها در یک ردیف
    keyboard.add(
        types.InlineKeyboardButton("📜 اشتراک‌های من", callback_data="my_subs"),
        types.InlineKeyboardButton("🧾 فاکتورهای من", callback_data="my_invoices")
    )
    keyboard.add(types.InlineKeyboardButton("👤 حساب کاربری", callback_data="account"))
    # جدا کردن پشتیبانی و آموزش
    keyboard.add(
        types.InlineKeyboardButton("📞 پشتیبانی", callback_data="support"),
        types.InlineKeyboardButton("📚 آموزش اتصال", callback_data="tutorial")
    )
    keyboard.add(types.InlineKeyboardButton("📊 وضعیت سرویس‌ها", callback_data="status"))
    return keyboard

@dp.message_handler(commands=['start'], state="*")
async def send_welcome(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("🌹 به ربات آراد وی‌آی‌پی خوش آمدید!\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:", 
                         reply_markup=main_menu_inline())

@dp.callback_query_handler(lambda c: c.data == "back_to_main", state="*")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text("🌹 منوی اصلی:\nلطفاً یک گزینه را انتخاب کنید:", reply_markup=main_menu_inline())

# --- بخش خرید و انتخاب سرویس ---
@dp.callback_query_handler(lambda c: c.data == "buy_menu", state="*")
async def buy_menu_types(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🛰 V2ray (نیم بها + نامحدود)", callback_data="type_v2ray"),
        types.InlineKeyboardButton("🚀 Biubiu VPN", callback_data="type_biubiu"),
        types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
    )
    await callback.message.edit_text("لطفا نوع سرویس را انتخاب کنید:", reply_markup=kb)

# --- تعرفه‌های Biubiu ---
@dp.callback_query_handler(lambda c: c.data == "type_biubiu")
async def biubiu_select_user(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👤 تک کاربره", callback_data="biu_single"),
        types.InlineKeyboardButton("👥 دو کاربره", callback_data="biu_double")
    )
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_menu"))
    await callback.message.edit_text("نوع اشتراک Biubiu را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("biu_"))
async def biubiu_plans_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    if "single" in callback.data:
        plans = [
            ("1ماهه نامحدود (تک) - 100,000", "100000"),
            ("2ماهه نامحدود (تک) - 200,000", "200000"),
            ("3ماهه نامحدود (تک) - 300,000", "300000")
        ]
    else:
        plans = [
            ("1ماهه نامحدود (دو) - 300,000", "300000"),
            ("3ماهه نامحدود (دو) - 600,000", "600000"),
            ("6ماهه نامحدود (دو) - 1,100,000", "1100000"),
            ("12ماهه نامحدود (دو) - 1,800,000", "1800000")
        ]
    
    for text, price in plans:
        kb.add(types.InlineKeyboardButton(f"{text} تومان", callback_data=f"set_Biubiu_{price}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="type_biubiu"))
    await callback.message.edit_text("یک پلن را انتخاب کنید:", reply_markup=kb)

# --- تعرفه‌های V2ray ---
@dp.callback_query_handler(lambda c: c.data == "type_v2ray")
async def v2ray_plans_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    v2_plans = ["5گیگ", "10گیگ", "20گیگ", "30گیگ", "50گیگ", "100گیگ"]
    for p in v2_plans:
        kb.add(types.InlineKeyboardButton(f"{p} زمان نامحدود - 100,000 تومان", callback_data=f"set_V2ray_{p}_100000"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_menu"))
    await callback.message.edit_text("پلن V2ray را انتخاب کنید:", reply_markup=kb)

# --- فرآیند دریافت نام کاربری ---
@dp.callback_query_handler(lambda c: c.data.startswith("set_"), state="*")
async def ask_username(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    await state.update_data(p_name=data[1], p_price=data[-1])
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🎲 نام کاربری تصادفی", callback_data="rand_uname"))
    kb.add(types.InlineKeyboardButton("❌ لغو خرید", callback_data="back_to_main"))
    
    await callback.message.edit_text("👤 یک نام کاربری (انگلیسی) تایپ و ارسال کنید یا دکمه تصادفی را بزنید:", reply_markup=kb)
    await BuyState.entering_username.set()

@dp.callback_query_handler(lambda c: c.data == "rand_uname", state=BuyState.entering_username)
async def rand_username(callback: types.CallbackQuery, state: FSMContext):
    uname = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    await state.update_data(username=uname)
    await show_final_invoice(callback.message, state)

@dp.message_handler(state=BuyState.entering_username)
async def custom_username(message: types.Message, state: FSMContext):
    if not re.match(r'^[a-zA-Z0-9_]+$', message.text):
        return await message.answer("❌ فقط حروف انگلیسی و عدد مجاز است!")
    await state.update_data(username=message.text)
    await show_final_invoice(message, state)

async def show_final_invoice(message: types.Message, state: FSMContext):
    data = await state.get_data()
    inv_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    await state.update_data(inv_id=inv_id)
    
    price_fmt = "{:,}".format(int(data['p_price']))
    text = (f"🧾 **فاکتور نهایی خرید**\n\n"
            f"🆔 شناسه فاکتور: `{inv_id}`\n"
            f"📦 سرویس: {data['p_name']}\n"
            f"👤 نام کاربری: `{data['username']}`\n"
            f"💰 مبلغ: {price_fmt} تومان\n\n"
            "برای پرداخت یکی از گزینه‌های زیر را انتخاب کنید:")
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💳 کارت به کارت", callback_data=f"pay_card_{inv_id}"))
    kb.add(types.InlineKeyboardButton("❌ لغو عملیات", callback_data="back_to_main"))
    
    if message.from_user.id == bot.id:
        await message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")

# --- پرداخت و تایید ادمین ---
@dp.callback_query_handler(lambda c: c.data.startswith("pay_card_"), state="*")
async def card_info(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    price_fmt = "{:,}".format(int(data.get('p_price', 0)))
    text = (f"💳 **اطلاعات واریز**\n\n"
            f"شماره کارت: `{CARD_NUMBER}`\n"
            f"به نام: {CARD_NAME}\n"
            f"مبلغ: {price_fmt} تومان\n\n"
            "📸 لطفاً تصویر رسید خود را اینجا ارسال کنید:")
    await callback.message.edit_text(text, parse_mode="Markdown")
    await BuyState.waiting_for_receipt.set()

@dp.message_handler(content_types=['photo'], state=BuyState.waiting_for_receipt)
async def admin_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.answer("✅ رسید با موفقیت ارسال شد. پس از تایید مدیریت، اشتراک شما فعال می‌شود.", 
                         reply_markup=main_menu_inline())
    
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ تایید", callback_data=f"adm_ok_{message.from_user.id}_{data['inv_id']}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"adm_no_{message.from_user.id}_{data['inv_id']}")
    )
    
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"🔔 رسید جدید!\nکاربر: {message.from_user.id}\nفاکتور: {data['inv_id']}", 
                         reply_markup=kb)
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith("adm_"), state="*")
async def admin_verify(callback: types.CallbackQuery):
    _, action, uid, inv = callback.data.split("_")
    if action == "ok":
        await bot.send_message(uid, f"🎉 فاکتور {inv} تایید شد! اکانت شما در حال آماده‌سازی است.")
        await callback.message.edit_caption(caption=f"✅ تایید شد (کاربر {uid})")
    else:
        await bot.send_message(uid, f"❌ رسید فاکتور {inv} رد شد. لطفاً مجدد تلاش کنید.")
        await callback.message.edit_caption(caption=f"❌ رد شد (کاربر {uid})")
    await callback.answer()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
