import random, string, datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from loader import dp, bot, ADMIN_ID
from database import get_user, users_col, add_invoice
import markups as nav

class BuyState(StatesGroup):
    entering_username = State()
    waiting_for_receipt = State()

# این رو همون بالا، زیر ایمپورت‌ها بذار
def generate_random_username():
    chars = string.ascii_lowercase + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(6))
    return f"AradVIP_{random_part}"


# --- ۱. دستور استارت ---
@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message):
    await get_user(message.from_user.id)
    await message.answer("✨ به ربات آراد VIP خوش آمدید\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=nav.main_menu())

# --- ۲. حساب کاربری (فارسی) ---
@dp.callback_query_handler(lambda c: c.data == "my_account", state="*")
async def my_account(callback: types.CallbackQuery):
    user = await users_col.find_one({"user_id": callback.from_user.id})
    wallet = user.get('wallet', 0)
    text = (
        f"👤 **اطلاعات حساب شما**\n\n"
        f"🆔 آیدی عددی: `{callback.from_user.id}`\n"
        f"💰 موجودی کیف پول: {wallet:,} تومان\n"
        f"🎁 تعداد زیرمجموعه: {user.get('ref_count', 0)} نفر\n\n"
        f"وضعیت حساب: فعال ✅"
    )
    await callback.message.edit_text(text, reply_markup=nav.main_menu(), parse_mode="Markdown")

# --- ۳. تعرفه‌ها (فارسی و مرتب شده از راست به چپ) ---
@dp.callback_query_handler(lambda c: c.data == "buy_v2ray")
async def v2ray_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    plans = [
        ("5GB - 100,000 تومان", 100000, "5GB"),
        ("10GB - 150,000 تومان", 150000, "10GB"),
        ("20GB - 200,000 تومان", 200000, "20GB"),
        ("30GB - 250,000 تومان", 250000, "30GB"),
        ("50GB - 350,000 تومان", 350000, "50GB"),
        ("100GB - 500,000 تومان", 500000, "100GB"),
        ("200GB - 800,000 تومان", 800000, "200GB"),
        ("300GB - 1,100,000 تومان", 1100000, "300GB"),
    ]
    for text, price, name in plans:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"plan_v2ray_{price}_{name}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new"))
    await callback.message.edit_text("🛒 لیست پلن‌های V2ray (زمان نامحدود):", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("biu_"))
async def biubiu_plans(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    kb = types.InlineKeyboardMarkup(row_width=1)
    if mode == "1":
        plans = [("1 ماهه - 100,000 تومان", 100000, "B1-1M"), ("2 ماهه - 200,000 تومان", 200000, "B1-2M"), ("3 ماهه - 300,000 تومان", 300000, "B1-3M")]
    else:
        plans = [
            ("1 ماهه - 300,000 تومان", 300000, "B2-1M"), 
            ("3 ماهه - 600,000 تومان", 600000, "B2-3M"), 
            ("6 ماهه - 1,100,000 تومان", 1100000, "B2-6M"), 
            ("12 ماهه - 1,800,000 تومان", 1800000, "B2-12M")
        ]
    for text, price, name in plans:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"plan_biu_{price}_{name}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_biubiu"))
    await callback.message.edit_text("🛒 پلن مورد نظر Biubiu را انتخاب کنید:", reply_markup=kb)

# --- دریافت نام کاربری با دکمه نام تصادفی ---
@dp.callback_query_handler(lambda c: c.data.startswith("plan_"), state="*")
async def ask_username(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    # ذخیره اطلاعات پلن در حافظه موقت
    await state.update_data(price=int(parts[2]), plan_name=parts[3], s_type=parts[1])
    await BuyState.entering_username.set()
    
    # ساخت دکمه برای تولید اسم رندوم
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🎲 انتخاب نام تصادفی (AradVIP_xxxx)", callback_data="random_name")
    )
    await callback.message.answer("👤 یک نام کاربری (انگلیسی) ارسال کنید یا دکمه زیر را بزنید:", reply_markup=kb)

# --- این هندلر رو هم دقیقاً زیر همین کد قبلی اضافه کن ---
@dp.callback_query_handler(lambda c: c.data == "random_name", state=BuyState.entering_username)
async def handle_random_name(callback: types.CallbackQuery, state: FSMContext):
    r_name = generate_random_username()
    # آپدیت کردن یوزرنیم در دیتای استیت
    await state.update_data(username=r_name)
    
    # ساخت پیام مجازی برای فرستادن به مرحله بعد
    msg = types.Message(text=r_name, from_user=callback.from_user, chat=callback.message.chat)
    await create_invoice(msg, state) # صدا کردن مرحله صدور فاکتور
    await callback.answer(f"نام انتخاب شد: {r_name}")


@dp.message_handler(state=BuyState.entering_username)
async def create_invoice(message: types.Message, state: FSMContext):
    username = message.text.strip().lower()
    data = await state.get_data()
    inv = await add_invoice(message.from_user.id, {'price': data['price'], 'plan': data['plan_name'], 'type': data['s_type'], 'username': username})
    
    text = (
        f"🧾 **فاکتور پرداخت**\n\n"
        f"🔹 نوع سرویس: {data['s_type'].upper()}\n"
        f"📦 پلن: {data['plan_name']}\n"
        f"👤 نام کاربری: `{username}`\n"
        f"💰 مبلغ قابل پرداخت: **{data['price']:,} تومان**\n\n"
        f"لطفاً روش پرداخت را انتخاب کنید:"
    )
    kb = types.InlineKeyboardMarkup(row_width=2).add(
        types.InlineKeyboardButton("💳 کارت به کارت", callback_data=f"pay_card_{inv['inv_id']}"),
        types.InlineKeyboardButton("💰 پرداخت با کیف پول", callback_data=f"pay_wallet_{inv['inv_id']}")
    )
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

# --- ۵. پرداخت کارت به کارت (کپی آسان) ---
@dp.callback_query_handler(lambda c: c.data.startswith("pay_card_"), state="*")
async def card_payment(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    price = data.get('price', 0)
    await BuyState.waiting_for_receipt.set()
    
    text = (
        f"📌 **راهنمای واریز**\n\n"
        f"مبلغ **{price:,} تومان** را به شماره کارت زیر واریز کنید:\n\n"
        f"💳 شماره کارت: `5057851560122222`\n"
        f"👤 بنام: **سجاد رستگاران**\n\n"
        f"📸 پس از واریز، رسید را اینجا ارسال کنید."
    )
    await callback.message.answer(text, parse_mode="Markdown")

@dp.message_handler(content_types=['photo'], state=BuyState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.answer("✅ رسید دریافت شد. منتظر تایید مدیریت بمانید.")
    
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✅ تایید و ارسال اشتراک", callback_data=f"admin_ok_{message.from_user.id}_{data['price']}"),
        types.InlineKeyboardButton("❌ رد رسید", callback_data=f"admin_no_{message.from_user.id}_0")
    )
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"💰 رسید جدید\n👤 کاربر: `{message.from_user.id}`\n💵 مبلغ: {data['price']:,}\n📦 پلن: {data['plan_name']}\n👤 یوزرنیم: {data.get('username')}", 
                         reply_markup=kb, parse_mode="Markdown")
    await state.finish()

# --- ۶. پرداخت مستقیم با کیف پول ---
@dp.callback_query_handler(lambda c: c.data.startswith("pay_wallet_"), state="*")
async def wallet_payment(callback: types.CallbackQuery, state: FSMContext):
    user = await users_col.find_one({"user_id": callback.from_user.id})
    data = await state.get_data()
    price = data.get('price', 0)
    
    if user.get('wallet', 0) >= price:
        await users_col.update_one({"user_id": callback.from_user.id}, {"$inc": {"wallet": -price}})
        await bot.send_message(ADMIN_ID, f"🚀 **خرید جدید با کیف پول**\n👤 کاربر: `{callback.from_user.id}`\n📦 پلن: {data['plan_name']}\n👤 یوزرنیم: {data.get('username')}")
        await callback.message.edit_text("✅ پرداخت موفق! سفارش شما برای مدیریت ارسال شد. اشتراک شما به زودی ارسال می‌شود.")
        await state.finish()
    else:
        await callback.answer("❌ موجودی کیف پول کافی نیست!", show_alert=True)
