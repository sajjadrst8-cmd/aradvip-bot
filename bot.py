import logging
import os
import random
import string
import datetime
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from motor.motor_asyncio import AsyncIOMotorClient

# --- تنظیمات ---
API_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
ADMIN_ID = 863961919
CARD_NUMBER = "5057851560122222"
CARD_NAME = "سجاد رستگاران"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

cluster = AsyncIOMotorClient(MONGO_URL)
db = cluster["arad_database"]
users_col = db["users"]

class BotState(StatesGroup):
    entering_amount = State()
    entering_username = State()
    waiting_for_receipt = State()

async def get_user(user_id, referrer=None):
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        user = {"user_id": user_id, "wallet": 0, "referred_by": int(referrer) if (referrer and referrer.isdigit()) else None, "join_date": datetime.datetime.now().strftime("%Y/%m/%d")}
        await users_col.insert_one(user)
    return user

def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🛍 خرید اشتراک", callback_data="buy_menu"),
           types.InlineKeyboardButton("👤 حساب کاربری", callback_data="account"))
    kb.add(types.InlineKeyboardButton("📞 پشتیبانی", callback_data="support"),
           types.InlineKeyboardButton("👥 زیرمجموعه‌گیری", callback_data="ref_system"))
    return kb

@dp.message_handler(commands=['start'], state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await get_user(message.from_user.id, message.get_args())
    await message.answer("🌹 به آراد وی‌آی‌پی خوش آمدید!", reply_markup=main_menu())

# --- منوی خرید ---
@dp.callback_query_handler(lambda c: c.data == "buy_menu", state="*")
async def buy_menu(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("🛰 V2ray (نیم بها)", callback_data="type_v2ray"),
           types.InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu"))
    await callback.message.edit_text("نوع سرویس:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "type_v2ray")
async def v2ray_plans(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    v2_list = [("5گیگ زمان نامحدود 100 هزار تومان", "100000"), ("10گیگ زمان نامحدود 100 هزار تومان", "100000")] # لیست رو طبق قبل کامل کن
    for text, price in v2_list:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"set_buy_V2ray_{price}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_menu"))
    await callback.message.edit_text("پلن مورد نظر:", reply_markup=kb)

# --- دریافت یوزرنیم ---
@dp.callback_query_handler(lambda c: c.data.startswith("set_buy_"), state="*")
async def ask_user(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    await state.update_data(p_name=data[2], p_price=data[3])
    await BotState.entering_username.set()
    await callback.message.answer("👤 نام کاربری انگلیسی برای اکانت بفرستید:")

@dp.message_handler(state=BotState.entering_username)
async def get_user_buy(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    data = await state.get_data()
    price = int(data['p_price'])
    user = await get_user(message.from_user.id)
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(f"💳 کارت به کارت ({price:,} تومان)", callback_data="pay_card"))
    kb.add(types.InlineKeyboardButton(f"💰 پرداخت از کیف پول (موجودی: {user['wallet']:,})", callback_data="pay_wallet"))
    kb.add(types.InlineKeyboardButton("❌ لغو", callback_data="main_menu"))
    
    await message.answer(f"🧾 فاکتور نهایی\n💰 مبلغ: {price:,} تومان\n👤 یوزرنیم: {message.text}\n\nروش پرداخت را انتخاب کنید:", reply_markup=kb)

# --- پرداخت با کیف پول ---
@dp.callback_query_handler(lambda c: c.data == "pay_wallet", state=BotState.entering_username)
async def wallet_pay(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    price = int(data['p_price'])
    user = await get_user(callback.from_user.id)
    
    if user['wallet'] >= price:
        # کسر از موجودی
        await users_col.update_one({"user_id": callback.from_user.id}, {"$inc": {"wallet": -price}})
        await callback.message.edit_text("✅ پرداخت با موفقیت انجام شد!\nسرویس شما به زودی ارسال می‌شود.")
        # اطلاع به ادمین
        await bot.send_message(ADMIN_ID, f"🆕 خرید جدید (پرداخت با کیف پول)\n👤 کاربر: {callback.from_user.id}\n📦 پلن: {data['p_name']}\n🔑 یوزر: {data['username']}")
        await state.finish()
    else:
        await callback.answer("❌ موجودی کافی نیست! حساب خود را شارژ کنید.", show_alert=True)

# --- پرداخت کارت به کارت ---
@dp.callback_query_handler(lambda c: c.data == "pay_card", state=BotState.entering_username)
async def card_pay(callback: types.CallbackQuery):
    await callback.message.edit_text(f"💳 شماره کارت: `{CARD_NUMBER}`\n👤 بنام: {CARD_NAME}\n\n📸 رسید واریز را بفرستید:")
    await BotState.waiting_for_receipt.set()

# --- تایید رسید توسط ادمین ---
@dp.message_handler(content_types=['photo'], state=BotState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✅ تایید", callback_data=f"adm_ok_{message.from_user.id}_{data.get('p_price',0)}_BUY"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"adm_no_{message.from_user.id}")
    )
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"رسید خرید\nکاربر: {message.from_user.id}\nیوزرنیم: {data.get('username')}", reply_markup=kb)
    await message.answer("✅ رسید برای ادمین ارسال شد.")
    await state.finish()

# بخش افزایش موجودی و ادمین (مشابه قبل با متد update_one مانگو) رو هم به همین ترتیب چک کن.

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
