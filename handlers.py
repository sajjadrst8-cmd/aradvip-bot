import random, string, datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from loader import dp, bot, ADMIN_ID
from database import get_user, users_col, add_invoice
import markups as nav
import config

class BuyState(StatesGroup):
    entering_username = State()
    waiting_for_receipt = State()
    entering_custom_amount = State()

def generate_random_username():
    chars = string.ascii_lowercase + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(6))
    return f"AradVIP_{random_part}"

# --- ۱. دستور استارت ---
@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    
    args = message.get_args()
    referrer_id = args if args.isdigit() else None
    await get_user(message.from_user.id, referrer_id)
    
    # ارسال دستور حذف کیبورد بزرگ به همراه منوی اصلی در یک پیام
    # این کد دکمه‌های خرید اشتراک و ... که پایین صفحه چسبیده بودن رو پاک میکنه
    await message.answer(
        "✨ به ربات آراد VIP خوش آمدید\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:", 
        reply_markup=nav.main_menu()
    )

# --- ۲. حساب کاربری و زیرمجموعه ---
@dp.callback_query_handler(lambda c: c.data == "my_account", state="*")
async def my_account_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    user = await users_col.find_one({"user_id": callback.from_user.id})
    wallet = user.get('wallet', 0)
    ref_count = user.get('ref_count', 0)
    
    text = (
        f"👤 **جزئیات حساب کاربری**\n\n"
        f"💰 موجودی کیف پول: **{wallet:,} تومان**\n"
        f"👥 تعداد زیرمجموعه: **{ref_count} نفر**\n\n"
        f"یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    await callback.message.edit_text(text, reply_markup=nav.account_menu(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "referral_section", state="*")
async def referral_handler(callback: types.CallbackQuery):
    user = await users_col.find_one({"user_id": callback.from_user.id})
    bot_info = await bot.get_me()
    invite_link = f"https://t.me/{bot_info.username}?start={callback.from_user.id}"
    
    text = (
        f"💰 **سیستم کسب درآمد (زیرمجموعه‌گیری)**\n\n"
        f"👥 تعداد زیرمجموعه‌های شما: **{user.get('ref_count', 0)} نفر**\n"
        f"🎁 پاداش شما: **۱۰٪ از هر خرید زیرمجموعه**\n\n"
        f"🔗 **لینک دعوت اختصاصی شما:**\n"
        f"`{invite_link}`"
    )
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🔙 بازگشت به حساب کاربری", callback_data="my_account")
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

# --- ۳. خرید سرویس جدید ---
@dp.callback_query_handler(lambda c: c.data == "buy_new", state="*")
async def buy_new_handler(callback: types.CallbackQuery):
    await callback.message.edit_text("لطفاً نوع سرویس مورد نظر خود را انتخاب کنید:", reply_markup=nav.buy_menu())

@dp.callback_query_handler(lambda c: c.data == "buy_v2ray")
async def v2ray_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for text, price, name in config.V2RAY_PLANS:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"plan_v2ray_{price}_{name}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new"))
    await callback.message.edit_text("🛒 لیست پلن‌های V2ray:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "buy_biubiu")
async def biubiu_user_choice(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("👤 ۱ کاربره", callback_data="biu_1"),
           types.InlineKeyboardButton("👥 ۲ کاربره", callback_data="biu_2"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new"))
    await callback.message.edit_text("تعداد کاربر اکانت Biubiu را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("biu_"))
async def biubiu_plans(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    kb = types.InlineKeyboardMarkup(row_width=1)
    plans = config.BIUBIU_1U_PLANS if mode == "1" else config.BIUBIU_2U_PLANS
    for text, price, name in plans:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"plan_biu_{price}_{name}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_biubiu"))
    await callback.message.edit_text("🛒 پلن مورد نظر Biubiu را انتخاب کنید:", reply_markup=kb)

# --- ۴. دریافت نام کاربری و صدور فاکتور ---
async def proceed_to_invoice(message: types.Message, state: FSMContext, username: str):
    data = await state.get_data()
    price = data.get('price')
    s_type = data.get('s_type')
    plan_name = data.get('plan_name')

    display_plan = plan_name
    if s_type == "biu":
        parts = plan_name.split('-')
        users = "1u" if "1" in parts[0] else "2u"
        display_plan = f"BiuBiu_{parts[1].lower() if len(parts)>1 else ''}{users}"
    elif s_type == "v2ray":
        display_plan = f"V2ray_{plan_name}"

    inv = await add_invoice(message.chat.id, {
        'price': price, 'plan': display_plan, 
        'type': s_type, 'username': username
    })
    
    text = (
        f"🧾 **فاکتور پرداخت آراد VIP**\n\n"
        f"🔹 سرویس: **{s_type.upper()}**\n"
        f"📦 پلن: `{display_plan}`\n"
        f"👤 نام کاربری: `{username}`\n"
        f"💰 مبلغ: **{price:,} تومان**\n\n"
        f"👇 روش پرداخت را انتخاب کنید:"
    )
    await bot.send_message(message.chat.id, text, reply_markup=nav.payment_methods(inv['inv_id']), parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data.startswith("plan_"), state="*")
async def ask_username(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    await state.update_data(s_type=parts[1], price=int(parts[2]), plan_name=parts[3])
    await BuyState.entering_username.set()
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🎲 انتخاب نام تصادفی", callback_data="random_name"))
    await callback.message.answer("👤 یک نام کاربری (انگلیسی) ارسال کنید یا دکمه زیر را بزنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "random_name", state=BuyState.entering_username)
async def handle_random_name(callback: types.CallbackQuery, state: FSMContext):
    r_name = generate_random_username()
    await state.update_data(username=r_name)
    await callback.answer(f"✅ نام نهایی شد: {r_name}")
    await callback.message.delete()
    await proceed_to_invoice(callback.message, state, r_name)

@dp.message_handler(state=BuyState.entering_username)
async def handle_manual_username(message: types.Message, state: FSMContext):
    username = message.text.strip().lower()
    if not username.replace("_", "").isalnum():
        return await message.answer("❌ نام کاربری فقط باید شامل حروف انگلیسی و عدد باشد.")
    await state.update_data(username=username)
    await proceed_to_invoice(message, state, username)

# --- ۵. بخش شارژ کیف پول (اصلاح شده) ---
@dp.callback_query_handler(lambda c: c.data == "charge_wallet", state="*")
async def wallet_main_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    text = "💳 **بخش شارژ کیف پول**\n\nلطفاً یک مبلغ را انتخاب کنید یا مبلغ دلخواه خود را وارد کنید:"
    try:
        await callback.message.edit_text(text, reply_markup=nav.wallet_charge_menu(), parse_mode="Markdown")
        await callback.answer()
    except:
        await callback.answer("خطا در لود منو")

@dp.callback_query_handler(lambda c: c.data == "charge_custom", state="*")
async def custom_amount_request(callback: types.CallbackQuery):
    await BuyState.entering_custom_amount.set()
    await callback.message.edit_text("✍️ لطفاً مبلغ مورد نظر خود را به **تومان** وارد کنید:\n(مثال: 150000)")
    await callback.answer()

@dp.message_handler(state=BuyState.entering_custom_amount)
async def process_custom_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ لطفاً فقط عدد انگلیسی وارد کنید!")
    
    amount = int(message.text)
    await state.update_data(charge_amount=amount)
    await BuyState.waiting_for_receipt.set()
    
    text = (f"✅ مبلغ درخواستی: {amount:,} تومان\n\n"
            f"💳 شماره کارت: `{config.CARD_NUMBER}`\n"
            f"👤 بنام: {config.CARD_NAME}\n\n"
            "📸 پس از واریز، عکس رسید را اینجا ارسال کنید.")
    await message.answer(text, parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data.startswith("charge_") and c.data != "charge_custom", state="*")
async def process_fixed_charge(callback: types.CallbackQuery, state: FSMContext):
    amount = int(callback.data.split("_")[1])
    await state.update_data(charge_amount=amount)
    await BuyState.waiting_for_receipt.set()
    
    text = (
        f"⏳ **درخواست شارژ: {amount:,} تومان**\n\n"
        f"💳 شماره کارت: `{config.CARD_NUMBER}`\n"
        f"👤 بنام: **{config.CARD_NAME}**\n\n"
        f"📸 لطفاً پس از واریز، تصویر رسید را ارسال کنید."
    )
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("❌ انصراف", callback_data="my_account"))
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

# --- ۶. فرآیند پرداخت و رسید ---
@dp.callback_query_handler(lambda c: c.data.startswith("pay_card_"), state="*")
async def card_payment(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await BuyState.waiting_for_receipt.set()
    text = (
        f"📌 **راهنمای واریز**\n\n"
        f"مبلغ **{data.get('price', 0):,} تومان** را واریز کنید:\n"
        f"💳 شماره کارت: `{config.CARD_NUMBER}`\n"
        f"👤 بنام: **{config.CARD_NAME}**\n\n"
        f"📸 رسید را اینجا ارسال کنید."
    )
    await callback.message.answer(text, parse_mode="Markdown")

@dp.message_handler(content_types=['photo'], state=BuyState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get('charge_amount') or data.get('price', 0)
    plan_info = data.get('plan_name', 'شارژ کیف پول')

    await message.answer("✅ رسید شما دریافت شد و برای مدیریت ارسال گردید. لطفاً تا تایید ادمین منتظر بمانید.")
    
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✅ تایید و واریز", callback_data=f"admin_ok_{message.from_user.id}_{amount}"),
        types.InlineKeyboardButton("❌ رد رسید", callback_data=f"admin_no_{message.from_user.id}_0")
    )
    
    caption = (
        f"💰 **رسید جدید جهت بررسی**\n\n"
        f"👤 کاربر: `{message.from_user.id}`\n"
        f"💵 مبلغ: **{amount:,} تومان**\n"
        f"📝 بابت: `{plan_info}`"
    )
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=kb, parse_mode="Markdown")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith("pay_wallet_"), state="*")
async def wallet_payment(callback: types.CallbackQuery, state: FSMContext):
    user = await users_col.find_one({"user_id": callback.from_user.id})
    data = await state.get_data()
    price = data.get('price', 0)
    
    if user.get('wallet', 0) >= price:
        await users_col.update_one({"user_id": callback.from_user.id}, {"$inc": {"wallet": -price}})
        await callback.message.edit_text("✅ پرداخت موفق! سفارش شما برای مدیریت ارسال شد.")
        await bot.send_message(ADMIN_ID, f"🚀 خرید با کیف پول\n👤 کاربر: `{callback.from_user.id}`\n💰 مبلغ: {price:,}")
        await state.finish()
    else:
        await callback.answer("❌ موجودی کافی نیست!", show_alert=True)

# --- ۷. هندلر ادمین ---
@dp.callback_query_handler(lambda c: c.data.startswith("admin_"), state="*")
async def admin_decision(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    action, user_id, price = parts[1], int(parts[2]), int(parts[3])
    
    if action == "ok":
        # --- بخش حیاتی: اضافه کردن موجودی به دیتابیس ---
        await users_col.update_one(
            {"user_id": user_id}, 
            {"$inc": {"wallet": price}} # مبلغ رو به کیف پول کاربر اضافه میکنه
        )
        
        # اطلاع‌رسانی به کاربر
        await bot.send_message(
            user_id, 
            f"✅ رسید شما تایید شد!\n💰 مبلغ **{price:,} تومان** به کیف پول شما اضافه شد."
        )
        
        # تغییر متن پیام برای ادمین که بدونه انجام شده
        await callback.message.edit_caption(
            caption=callback.message.caption + f"\n\n✅ تایید و مبلغ {price:,} واریز شد.", 
            reply_markup=None
        )
    else:
        await bot.send_message(user_id, "❌ رسید شما رد شد. در صورت لزوم به پشتیبانی پیام دهید.")
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n❌ رد شد.", 
            reply_markup=None
        )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "my_services", state="*")
async def my_services_list(callback: types.CallbackQuery):
    await callback.answer("📦 در حال حاضر سرویس فعالی برای شما ثبت نشده است.", show_alert=True)
