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


# --- بخش Biubiu VPN ---
@dp.callback_query_handler(lambda c: c.data == "buy_biubiu")
async def biubiu_menu(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("👤 تک کاربره", callback_data="biu_1"),
           types.InlineKeyboardButton("👥 دو کاربره", callback_data="biu_2"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new"))
    await callback.message.edit_text("لطفاً نوع اشتراک Biubiu را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("biu_"))
async def biubiu_plans(callback: types.CallbackQuery, state: FSMContext):
    mode = callback.data.split("_")[1]
    kb = types.InlineKeyboardMarkup(row_width=1)
    if mode == "1":
        plans = [("1ماهه نامحدود 100ت", 100000), ("2ماهه نامحدود 200ت", 200000), ("3ماهه نامحدود 300ت", 300000)]
    else:
        plans = [("1ماهه نامحدود 300ت", 300000), ("3ماهه نامحدود 600ت", 600000), ("6ماهه نامحدود 1100ت", 1100000), ("12ماهه نامحدود 1800ت", 1800000)]
    
    for text, price in plans:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"plan_biu_{price}_{text[:5]}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_biubiu"))
    await callback.message.edit_text("پلن مورد نظر را انتخاب کنید:", reply_markup=kb)

# --- بخش اشتراک تست ---
@dp.callback_query_handler(lambda c: c.data == "get_test")
async def test_menu(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("تست V2ray", callback_data="test_v2ray"),
           types.InlineKeyboardButton("تست Biubiu", callback_data="test_biubiu"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu"))
    await callback.message.edit_text("لطفاً نوع اشتراک تست را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("test_"))
async def process_test(callback: types.CallbackQuery):
    service = callback.data.split("_")[1]
    user = await users_col.find_one({"user_id": callback.from_user.id})
    
    if user['test_used'].get(service):
        await callback.answer("❌ شما قبلاً از این اشتراک تست استفاده کرده‌اید!", show_alert=True)
    else:
        await users_col.update_one({"user_id": user['user_id']}, {"$set": {f"test_used.{service}": True}})
        await callback.message.answer("⏳ درخواست شما در حال بررسی می‌باشد...")
        await bot.send_message(ADMIN_ID, f"🎁 درخواست تست جدید\nکاربر: {user['user_id']}\nنوع: {service}")

# --- بخش افزایش موجودی (شارژ کیف پول) ---
@dp.callback_query_handler(lambda c: c.data == "charge_wallet")
async def start_charge(callback: types.CallbackQuery):
    await BuyState.charging_wallet.set()
    await callback.message.answer("💰 مبلغ مورد نظر (تومان) را وارد کنید:\n(حداقل 70,000 و حداکثر 2,000,000)")

@dp.message_handler(state=BuyState.charging_wallet)
async def process_charge_amt(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ فقط عدد وارد کنید!")
    
    amt = int(message.text)
    if 70000 <= amt <= 2000000:
        inv = await add_invoice(message.from_user.id, {'price': amt, 'plan': 'شارژ حساب', 'type': '💰 شارژ کیف پول'})
        text = f"✅ فاکتور افزایش موجودی ایجاد شد.\n🧾 شناسه: `{inv['inv_id']}`\n💰 مبلغ: {amt:,} تومان"
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("💳 پرداخت کارت به کارت", callback_data=f"pay_{inv['inv_id']}"))
        await message.answer(text, reply_markup=kb)
        await state.finish()
    else:
        await message.answer("❌ مبلغ باید بین 70,000 تا 2,000,000 تومان باشد.")

# --- بخش زیرمجموعه‌گیری ---
@dp.callback_query_handler(lambda c: c.data == "ref_link")
async def get_ref(callback: types.CallbackQuery):
    bot_user = await bot.get_me()
    link = f"https://t.me/{bot_user.username}?start={callback.from_user.id}"
    text = (f"👥 سیستم زیرمجموعه‌گیری\n\n🔗 لینک اختصاصی شما:\n`{link}`\n\n"
            "🎁 دوستان خود را دعوت کنید و 10% سود دریافت کنید!")
    await callback.message.edit_text(text, reply_markup=nav.main_menu())

# --- کارت به کارت و ارسال رسید ---
@dp.callback_query_handler(lambda c: c.data == "method_card")
async def card_info(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    price = data.get('price', 'نامشخص')
    await BuyState.waiting_for_receipt.set()
    await callback.message.answer(
        f"💳 شماره کارت: `5057851560122222`\n👤 بنام: سجاد رستگاران\n💰 مبلغ: {price:,} تومان\n\n"
        "📸 تصویر رسید را بفرستید:", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("❌ لغو", callback_data="main_menu"))
    )

@dp.message_handler(content_types=['photo'], state=BuyState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.answer("✅ تصویر با موفقیت ارسال شد.\nلطفاً منتظر تأیید توسط پشتیبانی باشید (کمتر از 10 دقیقه).", 
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")))
    
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✅ تأیید", callback_data=f"admin_ok_{message.from_user.id}_{data.get('price', 0)}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"admin_no_{message.from_user.id}")
    )
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"💰 رسید جدید\nکاربر: {message.from_user.id}\nمبلغ: {data.get('price', 0)}", reply_markup=kb)
    await state.finish()

# --- بخش کد تخفیف ---
@dp.callback_query_handler(lambda c: c.data == "apply_off")
async def ask_promo(callback: types.CallbackQuery):
    await BuyState.entering_offcode.set()
    await callback.message.answer("🎟 لطفا کد تخفیف خود را وارد کنید:")

@dp.message_handler(state=BuyState.entering_offcode)
async def check_promo(message: types.Message, state: FSMContext):
    promo = message.text
    # به عنوان مثال یک کد ثابت: Arad2024
    if promo == "Arad2024":
        await message.answer("✅ کد تخفیف معتبر بود! 20% تخفیف اعمال شد.")
        # اینجا منطق کسر مبلغ را اضافه کن
    else:
        await message.answer("❌ کد تخفیف نامعتبر است.")
    await state.finish()

# --- پنل مدیریت اختصاصی ---

@dp.message_handler(commands=['admin'], user_id=ADMIN_ID)
async def admin_panel(message: types.Message):
    text = (
        "🛠 **پنل مدیریت آراد وی‌آی‌پی**\n\n"
        "برای تغییر موجودی کاربر از دستور زیر استفاده کنید:\n"
        "`/setwallet [آیدی‌عددی] [مبلغ]`\n\n"
        "مثال برای شارژ 50 هزار تومان:\n"
        "`/setwallet 12345678 50000`"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message_handler(commands=['setwallet'], user_id=ADMIN_ID)
async def set_wallet_manual(message: types.Message):
    args = message.get_args().split()
    if len(args) == 2:
        target_id, amount = args[0], args[1]
        try:
            await users_col.update_one({"user_id": int(target_id)}, {"$set": {"wallet": float(amount)}})
            await message.answer(f"✅ موجودی کاربر {target_id} با موفقیت به {amount} تغییر یافت.")
            await bot.send_message(target_id, f"💰 موجودی حساب شما توسط مدیریت به {amount} تومان تغییر یافت.")
        except Exception as e:
            await message.answer(f"❌ خطایی رخ داد: {e}")
    else:
        await message.answer("⚠️ فرمت اشتباه! مثال: `/setwallet 1234567 50000`")
