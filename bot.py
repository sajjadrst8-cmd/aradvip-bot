import logging, os, datetime
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from motor.motor_asyncio import AsyncIOMotorClient

# --- تنظیمات سیستمی ---
API_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
ADMIN_ID = 863961919
CARD_NUMBER = "5057851560122222"
CARD_NAME = "سجاد رستگاران"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- اتصال به MongoDB ---
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
        user = {
            "user_id": user_id, 
            "wallet": 0, 
            "referred_by": int(referrer) if (referrer and str(referrer).isdigit()) else None, 
            "join_date": datetime.datetime.now().strftime("%Y/%m/%d")
        }
        await users_col.insert_one(user)
    return user

# --- کیبورد اصلی (دقیقاً طبق اسکرین‌شات شما) ---
def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("🛍 خرید اشتراک جدید", callback_data="buy_menu"),
           types.InlineKeyboardButton("🎁 دریافت اشتراک تست", callback_data="get_test"))
    kb.add(types.InlineKeyboardButton("📜 اشتراک‌های من", callback_data="my_subs"),
           types.InlineKeyboardButton("🧾 فاکتورهای من", callback_data="my_invoices"))
    kb.add(types.InlineKeyboardButton("👤 حساب کاربری", callback_data="account"))
    kb.add(types.InlineKeyboardButton("📞 پشتیبانی", callback_data="support"),
           types.InlineKeyboardButton("📚 آموزش اتصال", callback_data="learn_connect"))
    kb.add(types.InlineKeyboardButton("📊 وضعیت سرویس‌ها", callback_data="server_status"),
           types.InlineKeyboardButton("👥 زیرمجموعه‌گیری", callback_data="ref_system"))
    return kb

# --- شروع ربات ---
@dp.message_handler(commands=['start'], state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    args = message.get_args()
    await get_user(message.from_user.id, args)
    await message.answer(f"🌹 سلام {message.from_user.first_name}، به آراد وی‌آی‌پی خوش آمدید!", reply_markup=main_menu())

# --- منوی خرید و V2ray ---
@dp.callback_query_handler(lambda c: c.data == "buy_menu", state="*")
async def buy_menu(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("🛰 V2ray (نیم بها)", callback_data="type_v2ray"),
           types.InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu"))
    await callback.message.edit_text("لطفاً نوع سرویس خود را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "type_v2ray")
async def v2ray_plans(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    v2_list = [
        ("5گیگ زمان نامحدود 100,000 تومان", "100000"),
        ("10گیگ زمان نامحدود 150,000 تومان", "150000"),
        ("20گیگ زمان نامحدود 200,000 تومان", "200000"),
        ("50گیگ زمان نامحدود 350,000 تومان", "350000")
    ]
    for text, price in v2_list:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"set_buy_V2ray_{price}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_menu"))
    await callback.message.edit_text("🛰 لیست تعرفه‌های V2ray:", reply_markup=kb)

# --- فرآیند خرید و دریافت یوزرنیم ---
@dp.callback_query_handler(lambda c: c.data.startswith("set_buy_"), state="*")
async def ask_username(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    await state.update_data(p_name=data[2], p_price=data[3])
    await BotState.entering_username.set()
    await callback.message.answer("👤 نام کاربری مورد نظر برای اشتراک را به انگلیسی بفرستید:")

@dp.message_handler(state=BotState.entering_username)
async def process_buy_final(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    data = await state.get_data()
    price = int(data['p_price'])
    user = await get_user(message.from_user.id)
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(f"💰 پرداخت از کیف پول (موجودی: {user['wallet']:,})", callback_data="pay_wallet"))
    kb.add(types.InlineKeyboardButton(f"💳 کارت به کارت ({price:,} تومان)", callback_data="pay_card"))
    kb.add(types.InlineKeyboardButton("❌ انصراف", callback_data="main_menu"))
    
    await message.answer(f"🧾 فاکتور نهایی\n📦 سرویس: {data['p_name']}\n💰 مبلغ: {price:,} تومان\n👤 یوزرنیم: {message.text}\n\nروش پرداخت را انتخاب کنید:", reply_markup=kb)

# --- کسر از کیف پول (بدون نیاز به تایید ادمین) ---
@dp.callback_query_handler(lambda c: c.data == "pay_wallet", state=BotState.entering_username)
async def wallet_pay_exec(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    price = int(data['p_price'])
    user = await get_user(callback.from_user.id)
    
    if user['wallet'] >= price:
        await users_col.update_one({"user_id": callback.from_user.id}, {"$inc": {"wallet": -price}})
        await callback.message.edit_text("✅ پرداخت با موفقیت از کیف پول شما انجام شد!\nسرویس شما به زودی توسط ادمین فعال و ارسال می‌شود.")
        await bot.send_message(ADMIN_ID, f"🔔 **خرید جدید با کیف پول**\n👤 کاربر: {callback.from_user.id}\n📦 پلن: {data['p_name']}\n🔑 یوزرنیم: {data['username']}")
        await state.finish()
    else:
        await callback.answer("❌ موجودی کیف پول شما کافی نیست!", show_alert=True)

# --- افزایش موجودی (شارژ حساب) ---
@dp.callback_query_handler(lambda c: c.data == "account")
async def view_account(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    text = f"👤 حساب کاربری شما\n\n💰 موجودی: {user['wallet']:,} تومان\n📅 تاریخ عضویت: {user['join_date']}"
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("➕ شارژ کیف پول", callback_data="add_balance"))
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "add_balance")
async def start_charge(callback: types.CallbackQuery):
    await BotState.entering_amount.set()
    await callback.message.answer("💰 مبلغ شارژ را به تومان وارد کنید:")

@dp.message_handler(state=BotState
