import random, string, datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from main import dp, bot, ADMIN_ID
from database import get_user, users_col, add_invoice
import markups as nav

class BuyState(StatesGroup):
    entering_username = State()
    entering_offcode = State()
    waiting_for_receipt = State()
    charging_wallet = State()

# --- شروع فرآیند خرید ---
@dp.callback_query_handler(lambda c: c.data == "buy_new")
async def buy_start(callback: types.CallbackQuery):
    await callback.message.edit_text("لطفاً نوع اشتراک خودتون رو انتخاب کنید:", reply_markup=nav.buy_menu())

# --- لیست تعرفه‌های V2ray ---
@dp.callback_query_handler(lambda c: c.data == "buy_v2ray")
async def v2ray_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    plans = [
        ("5گیگ زمان نامحدود ۱۰۰ هزار تومان", 100000),
        ("10گیگ زمان نامحدود ۱۰۰ هزار تومان", 100000),
        ("20گیگ زمان نامحدود ۱۰۰ هزار تومان", 100000),
        ("30گیگ زمان نامحدود ۱۰۰ هزار تومان", 100000),
        ("50گیگ زمان نامحدود ۱۰۰ هزار تومان", 100000),
        ("100گیگ زمان نامحدود ۱۰۰ هزار تومان", 100000),
        ("200گیگ زمان نامحدود ۱۰۰ هزار تومان", 100000),
        ("300گیگ زمان نامحدود ۱۰۰ هزار تومان", 100000),
    ]
    for text, price in plans:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"plan_v2ray_{price}_{text[:5]}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new"))
    await callback.message.edit_text("لطفاً پلن مورد نظر خودتون رو انتخاب کنید:", reply_markup=kb)

# --- دریافت نام کاربری با ضوابط ---
@dp.callback_query_handler(lambda c: c.data.startswith("plan_"))
async def ask_username(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    await state.update_data(price=int(parts[2]), plan_name=parts[3], type="V2ray")
    await BuyState.entering_username.set()
    
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🎲 نام تصادفی", callback_data="gen_rand"),
        types.InlineKeyboardButton("❌ لغو عملیات", callback_data="main_menu")
    )
    await callback.message.edit_text(
        "👤 لطفاً یک نام کاربری برای اشتراک وارد کنید.📌\n\n"
        "باید بین ۳ تا ۳۲ کاراکتر باشد و می‌تواند شامل عدد، حروف a-z و _ باشد.\n"
        "برای لغو روی دکمه لغو بزنید:", reply_markup=kb
    )

@dp.message_handler(state=BuyState.entering_username)
async def validate_username(message: types.Message, state: FSMContext):
    username = message.text.lower()
    # چک کردن ضوابط نام کاربری
    if len(username) < 3 or len(username) > 32 or not username.replace("_", "").isalnum():
        await message.answer("⚠️ نام کاربری نامعتبر است! طبق ضوابط گفته شده (3-32 کاراکتر، حروف و عدد) دوباره ارسال کنید:")
        return

    data = await state.get_data()
    inv = await add_invoice(message.from_user.id, {
        'price': data['price'], 'plan': data['plan_name'], 'type': data['type'], 'username': username
    })
    
    text = (
        f"✅ فاکتور شما با موفقیت ایجاد شد.\n\n"
        f"🧾 شناسه: `{inv['inv_id']}`\n"
        f"📌 وضعیت: 🟠 در انتظار\n"
        f"💰 مبلغ: {inv['amount']:,} تومان\n"
        f"📂 گروه: تانل نیم بها 🇮🇷(بدون محدودیت کاربر)\n"
        f"👤 کاربر: {username}\n"
        f"📆 تاریخ ثبت: {inv['date']}"
    )
    
    kb = types.InlineKeyboardMarkup(row_width=2).add(
        types.InlineKeyboardButton("💳 پرداخت فاکتور", callback_data=f"pay_{inv['inv_id']}"),
        types.InlineKeyboardButton("🎟 کد تخفیف", callback_data="apply_off"),
        types.InlineKeyboardButton("❌ لغو فاکتور", callback_data="main_menu")
    )
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

# --- مدیریت پرداخت با کیف پول ---
@dp.callback_query_handler(lambda c: c.data.startswith("pay_"), state="*")
async def payment_choice(callback: types.CallbackQuery, state: FSMContext):
    inv_id = callback.data.split("_")[1]
    await state.update_data(current_inv=inv_id)
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("💳 کارت به کارت", callback_data="method_card"),
        types.InlineKeyboardButton("💰 کیف پول", callback_data="method_wallet"),
        types.InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
    )
    await callback.message.edit_text("روش پرداخت را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "method_wallet", state="*")
async def wallet_pay(callback: types.CallbackQuery, state: FSMContext):
    user = await users_col.find_one({"user_id": callback.from_user.id})
    data = await state.get_data()
    # اینجا باید فاکتور را از دیتابیس بخوانی (من خلاصه می‌نویسم)
    price = data.get('price', 0)
    
    if user['wallet'] >= price:
        await users_col.update_one({"user_id": user['user_id']}, {"$inc": {"wallet": -price}})
        await callback.message.edit_text("✅ پرداخت با موفقیت انجام شد\nسرویس شما فعال گردید.", 
                                      reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("📦 اشتراک‌های من", callback_data="my_subs")))
        await state.finish()
    else:
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("➕ شارژ کیف پول", callback_data="charge_wallet"))
        await callback.message.answer("❌ موجودی شما کافی نیست! جهت پرداخت از کیف پول موجودی خود را شارژ نمایید", reply_markup=kb)

