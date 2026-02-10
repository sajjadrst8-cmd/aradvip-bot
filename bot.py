import asyncio
import logging
import random
import string
import os
from datetime import datetime
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

# ================= تنظیمات (دریافت از متغیرهای سیستم) =================
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
MONGO_URL = os.getenv("MONGO_URL")
REF_BONUS = 5000 
CARD_NUMBER = os.getenv("CARD_NUMBER", "5057851560122222")
CARD_NAME = os.getenv("CARD_NAME", "سجاد رستگاران")

logging.basicConfig(level=logging.INFO)

# ================= اتصال به دیتابیس ابری =================
client = AsyncIOMotorClient(MONGO_URL)
db = client["v2ray_store"]
users_col = db["users"]
invoices_col = db["invoices"]

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class BotStates(StatesGroup):
    entering_username = State()
    sending_receipt = State()

# ================= توابع کمکی دیتابیس =================
async def get_user(user_id):
    return await users_col.find_one({"user_id": user_id})

async def add_user(user_id, full_name, inviter=None):
    user = await get_user(user_id)
    if not user:
        new_user = {
            "user_id": user_id,
            "full_name": full_name,
            "balance": 0,
            "test_usage": 0,
            "joined_date": datetime.now().strftime("%Y/%m/%d"),
            "inviter_id": inviter
        }
        await users_col.insert_one(new_user)
        return True
    return False

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
    args = message.text.split()
    inviter_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    
    is_new = await add_user(uid, message.from_user.full_name, inviter_id)
    
    if is_new and inviter_id:
        await users_col.update_one({"user_id": inviter_id}, {"$inc": {"balance": REF_BONUS}})
        try:
            await bot.send_message(inviter_id, f"🎉 تبریک! یک زیرمجموعه جدید با لینک شما عضو شد.\n💰 هدیه: {REF_BONUS:,} تومان")
        except: pass

    await message.answer(f"سلام {message.from_user.first_name} خوش آمدید!", reply_markup=get_main_menu())

@dp.message(F.text == "حساب کاربری")
async def account_info(message: types.Message):
    user = await get_user(message.from_user.id)
    cursor = invoices_col.find({"user_id": message.from_user.id}).sort("date", -1).limit(3)
    purchases = await cursor.to_list(length=3)
    
    history = "\n".join([f"🔹 {p['plan_name']} | {p['status']}" for p in purchases]) if purchases else "سابقه‌ای ثبت نشده."

    text = (f"👤 <b>پنل کاربری</b>\n\n"
            f"💰 موجودی کیف پول: {user['balance']:,} تومان\n"
            f"📅 عضویت: {user['joined_date']}\n\n"
            f"📦 آخرین فعالیت‌ها:\n{history}")
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "زیرمجموعه گیری")
async def referral_info(message: types.Message):
    bot_user = await bot.get_me()
    ref_link = f"https://t.me/{bot_user.username}?start={message.from_user.id}"
    count = await users_col.count_documents({"inviter_id": message.from_user.id})
    
    text = (f"🤝 <b>برنامه دعوت دوستان</b>\n\n"
            f"با لینک زیر دوستان خود را دعوت کنید و با هر عضویت {REF_BONUS:,} تومان اعتبار بگیرید.\n\n"
            f"👥 زیرمجموعه‌های شما: {count} نفر\n"
            f"🔗 لینک شما:\n<code>{ref_link}</code>")
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "خرید اشتراک جدید")
async def buy_start(message: types.Message):
    kb = [[KeyboardButton(text="V2ray 20GB (150,000 تومان)")], [KeyboardButton(text="بازگشت")]]
    await message.answer("لطفا پلن را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@dp.message(F.text.contains("تومان"))
async def process_plan(message: types.Message, state: FSMContext):
    price = int(''.join(filter(str.isdigit, message.text.replace(',', ''))))
    await state.update_data(plan=message.text, price=price)
    await message.answer("👤 نام کاربری انگلیسی دلخواه خود را بفرستید:")
    await state.set_state(BotStates.entering_username)

@dp.message(BotStates.entering_username)
async def save_invoice(message: types.Message, state: FSMContext):
    data = await state.get_data()
    inv_id = "".join(random.choices(string.digits, k=6))
    
    invoice = {
        "_id": inv_id,
        "user_id": message.from_user.id,
        "plan_name": data['plan'],
        "amount": data['price'],
        "status": "⏳ در انتظار پرداخت",
        "alias": message.text,
        "date": datetime.now()
    }
    await invoices_col.insert_one(invoice)
    
    builder = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 پرداخت و ارسال رسید", callback_data=f"pay_{inv_id}")]
    ])
    await message.answer(f"📑 فاکتور {inv_id} صادر شد.\n💰 مبلغ: {data['price']:,} تومان", reply_markup=builder)
    await state.clear()

@dp.callback_query(F.data.startswith("pay_"))
async def pay_step(callback: types.CallbackQuery, state: FSMContext):
    inv_id = callback.data.split('_')[1]
    await state.update_data(curr_inv=inv_id)
    await callback.message.answer(f"💳 شماره کارت: `{CARD_NUMBER}`\n👤 بنام: {CARD_NAME}\n\n✅ پس از واریز، عکس رسید را بفرستید.")
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
    inv = await invoices_col.find_one({"_id": inv_id})
    if not inv: return
    
    if action == "ok":
        await invoices_col.update_one({"_id": inv_id}, {"$set": {"status": "✅ تایید شده"}})
        await bot.send_message(inv['user_id'], f"✅ پرداخت شما تایید شد!\n📦 سرویس {inv['plan_name']} برای شما فعال شد.")
    else:
        await invoices_col.update_one({"_id": inv_id}, {"$set": {"status": "❌ رد شده"}})
        await bot.send_message(inv['user_id'], "❌ رسید شما توسط مدیریت رد شد.")
    
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
        pass
