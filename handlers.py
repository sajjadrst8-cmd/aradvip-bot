import random, string, datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from loader import dp, bot, ADMIN_ID
from database import get_user, users_col, add_invoice
import markups as nav

class BuyState(StatesGroup):
    entering_username = State()
    entering_offcode = State()
    waiting_for_receipt = State()
    charging_wallet = State()

# --- ۱. دستور استارت ---
@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message):
    referrer = message.get_args()
    await get_user(message.from_user.id, referrer)
    await message.answer("✨ به ربات آراد VIP خوش آمدید\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=nav.main_menu())

# --- ۲. نمایش حساب کاربری ---
@dp.callback_query_handler(lambda c: c.data == "my_account", state="*")
async def my_account(callback: types.CallbackQuery):
    user = await users_col.find_one({"user_id": callback.from_user.id})
    text = (
        f"👤 **اطلاعات حساب شما**\n\n"
        f"🆔 آیدی عددی: `{callback.from_user.id}`\n"
        f"💰 موجودی کیف پول: {user['wallet']:,} تومان\n"
        f"🎁 تعداد زیرمجموعه: {user.get('ref_count', 0)} نفر"
    )
    await callback.message.edit_text(text, reply_markup=nav.main_menu(), parse_mode="Markdown")

# --- ۳. منوی خرید و V2ray (تعرفه‌های کامل) ---
@dp.callback_query_handler(lambda c: c.data == "buy_new")
async def buy_start(callback: types.CallbackQuery):
    await callback.message.edit_text("لطفاً نوع سرویس مورد نظر را انتخاب کنید:", reply_markup=nav.buy_menu())

@dp.callback_query_handler(lambda c: c.data == "buy_v2ray")
async def v2ray_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    plans = [
        ("5GB زمان نامحدود - ۱۰۰,۰۰۰ت", 100000, "5GB"),
        ("10GB زمان نامحدود - ۱۰۰,۰۰۰ت", 100000, "10GB"),
        ("20GB زمان نامحدود - ۱۰۰,۰۰۰ت", 100000, "20GB"),
        ("30GB زمان نامحدود - ۱۰۰,۰۰۰ت", 100000, "30GB"),
        ("50GB زمان نامحدود - ۱۰۰,۰۰۰ت", 100000, "50GB"),
        ("100GB زمان نامحدود - ۱۰۰,۰۰۰ت", 100000, "100GB"),
        ("200GB زمان نامحدود - ۱۰۰,۰۰۰ت", 100000, "200GB"),
        ("300GB زمان نامحدود - ۱۰۰,۰۰۰ت", 100000, "300GB"),
    ]
    for text, price, name in plans:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"plan_v2ray_{price}_{name}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new"))
    await callback.message.edit_text("🛒 لیست پلن‌های V2ray (نامحدود زمانی):", reply_markup=kb)

# --- ۴. بخش Biubiu VPN (اصلاح شده) ---
@dp.callback_query_handler(lambda c: c.data == "buy_biubiu")
async def biubiu_menu(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("👤 تک کاربره", callback_data="biu_1"),
           types.InlineKeyboardButton("👥 دو کاربره", callback_data="biu_2"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new"))
    await callback.message.edit_text("لطفاً تعداد کاربر اشتراک Biubiu را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("biu_"))
async def biubiu_plans(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    kb = types.InlineKeyboardMarkup(row_width=1)
    if mode == "1":
        plans = [("1ماهه نامحدود - ۱۰۰,۰۰۰ت", 100000, "B1-1M"), ("2ماهه نامحدود - ۲۰۰,۰۰۰ت", 200000, "B1-2M"), ("3ماهه نامحدود - ۳۰۰,۰۰۰ت", 300000, "B1-3M")]
    else:
        plans = [("1ماهه نامحدود - ۳۰۰,۰۰۰ت", 300000, "B2-1M"), ("3ماهه نامحدود - ۶۰۰,۰۰۰ت", 600000, "B2-3M"), ("12ماهه نامحدود - ۱,۸۰۰,۰۰۰ت", 1800000, "B2-12M")]
    
    for text, price, name in plans:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"plan_biu_{price}_{name}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_biubiu"))
    await callback.message.edit_text("🛒 پلن مورد نظر Biubiu را انتخاب کنید:", reply_markup=kb)

# --- ۵. دریافت نام کاربری و ایجاد فاکتور ---
@dp.callback_query_handler(lambda c: c.data.startswith("plan_"), state="*")
async def ask_username(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    # parts[1] نوع سرویس، parts[2] قیمت، parts[3] نام پلن
    await state.update_data(price=int(parts[2]), plan_name=parts[3], s_type=parts[1])
    await BuyState.entering_username.set()
    await callback.message.answer("👤 یک نام کاربری (انگلیسی) برای اشتراک خود ارسال کنید:\n(مثال: arad_user)")

@dp.message_handler(state=BuyState.entering_username)
async def create_invoice(message: types.Message, state: FSMContext):
    username = message.text.strip().lower()
    data = await state.get_data()
    inv = await add_invoice(message.from_user.id, {'price': data['price'], 'plan': data['plan_name'], 'type': data['s_type'], 'username': username})
    
    text = (
        f"🧾 **فاکتور پرداخت آراد VIP**\n\n"
        f"🔹 نوع سرویس: {data['s_type'].upper()}\n"
        f"📦 پلن: {data['plan_name']}\n"
        f"👤 نام کاربری: `{username}`\n"
        f"💰 مبلغ قابل پرداخت: **{data['price']:,} تومان**\n"
        f"🕒 تاریخ: {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n"
        f"لطفاً جهت فعال‌سازی، یکی از روش‌های پرداخت را انتخاب کنید:"
    )
    kb = types.InlineKeyboardMarkup(row_width=2).add(
        types.InlineKeyboardButton("💳 کارت به کارت", callback_data=f"pay_card_{inv['inv_id']}"),
        types.InlineKeyboardButton("💰 کیف پول", callback_data=f"pay_wallet_{inv['inv_id']}"),
        types.InlineKeyboardButton("🎟 کد تخفیف", callback_data="apply_off")
    )
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

# --- ۶. فرآیند پرداخت کارت به کارت ---
@dp.callback_query_handler(lambda c: c.data.startswith("pay_card_"), state="*")
async def card_payment(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    price = data.get('price', 0)
    await BuyState.waiting_for_receipt.set()
    
    text = (
        f"📌 **راهنمای پرداخت کارت به کارت**\n\n"
        f"مبلغ را به شماره کارت زیر واریز کنید:\n\n"
        f"💳 شماره کارت: `5057851560122222`\n"
        f"👤 بنام: **سجاد رستگاران**\n"
        f"🏦 بانک: **حکمت ایرانیان (سپه)**\n"
        f"💰 مبلغ دقیق: **{price:,} تومان**\n\n"
        f"📸 پس از واریز، عکس رسید را همین‌جا ارسال کنید."
    )
    await callback.message.answer(text, parse_mode="Markdown")

@dp.message_handler(content_types=['photo'], state=BuyState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.answer("✅ رسید شما دریافت شد و برای ادمین ارسال گردید. منتظر تایید باشید.")
    
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✅ تایید و شارژ", callback_data=f"admin_ok_{message.from_user.id}_{data['price']}"),
        types.InlineKeyboardButton("❌ رد رسید", callback_data=f"admin_no_{message.from_user.id}_0")
    )
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"💰 رسید جدید\n👤 آیدی کاربر: `{message.from_user.id}`\n💵 مبلغ: {data['price']:,}\n📂 پلن: {data['plan_name']}", 
                         reply_markup=kb, parse_mode="Markdown")
    await state.finish()

# --- ۷. تایید ادمین و پنل مدیریت ---
@dp.callback_query_handler(lambda c: c.data.startswith("admin_"), state="*")
async def admin_verify(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    status, uid, amt = parts[1], int(parts[2]), float(parts[3])

    if status == "ok":
        await users_col.update_one({"user_id": uid}, {"$inc": {"wallet": amt}})
        await bot.send_message(uid, f"✅ رسید شما تایید شد!\nمبلغ {amt:,} تومان به کیف پول شما اضافه شد.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ تایید شد.")
    else:
        await bot.send_message(uid, "❌ رسید شما رد شد. در صورت بروز مشکل با پشتیبانی در ارتباط باشید.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ رد شد.")
    await callback.answer()

@dp.message_handler(commands=['admin'], user_id=ADMIN_ID)
async def admin_panel(message: types.Message):
    await message.answer("🛠 پنل مدیریت\nشارژ کاربر: `/setwallet ID AMOUNT`", parse_mode="Markdown")

@dp.message_handler(commands=['setwallet'], user_id=ADMIN_ID)
async def set_wallet(message: types.Message):
    args = message.get_args().split()
    await users_col.update_one({"user_id": int(args[0])}, {"$set": {"wallet": float(args[1])}})
    await message.answer(f"✅ موجودی کاربر {args[0]} به {args[1]} تغییر یافت.")
