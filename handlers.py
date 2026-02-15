import random, string, datetime
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from loader import dp, bot, ADMIN_ID
from database import get_user, users_col, add_invoice
import markups as nav
import config
from bson import ObjectId

class BuyState(StatesGroup):
    entering_username = State()
    waiting_for_receipt = State()
    entering_custom_amount = State()
    waiting_for_test_choice = State() # اضافه شد

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
# --- نسخه نهایی هندلر ادمین (جایگزین کد قبلی شما) ---
@dp.callback_query_handler(lambda c: c.data.startswith("admin_"), state="*")
async def admin_decision(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    action, user_id, price = parts[1], int(parts[2]), int(parts[3])
    
    # پیدا کردن آخرین فاکتور در انتظار این کاربر برای ست کردن کانفیگ
    invoice = await invoices_col.find_one({"user_id": user_id, "status": "🟠 در انتظار"}, sort=[("_id", -1)])

    if action == "ok":
        if invoice:
            # بردن ادمین به وضعیت "انتظار برای ارسال کانفیگ"
            await state.set_state("wait_for_config")
            await state.update_data(target_user_id=user_id, target_inv_id=invoice['inv_id'], target_price=price)
            
            await callback.message.answer(f"✅ رسید تایید شد.\nحالا لطفاً **کانفیگ V2ray** یا لایسنس را ارسال کنید تا برای کاربر فعال شود:")
            # پاک کردن دکمه‌ها از روی رسید ادمین
            await callback.message.edit_reply_markup(reply_markup=None)
        else:
            # اگر به هر دلیلی فاکتوری پیدا نشد، باز هم کیف پول رو شارژ کن (پلن B)
            await users_col.update_one({"user_id": user_id}, {"$inc": {"wallet": price}})
            await bot.send_message(user_id, f"✅ رسید تایید شد و مبلغ {price:,} به کیف پول شما اضافه گشت.")
            await callback.answer("⚠️ فاکتوری پیدا نشد، فقط کیف پول شارژ شد.", show_alert=True)
            await callback.message.edit_reply_markup(reply_markup=None)
    else:
        # رد کردن رسید
        await bot.send_message(user_id, "❌ رسید شما توسط مدیریت رد شد.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ رد شد.", reply_markup=None)
    
    await callback.answer()

# --- حتماً این هندلر را هم بلافاصله بعد از کد بالا اضافه کنید ---
@dp.message_handler(state="wait_for_config", user_id=ADMIN_ID)
async def receive_config_from_admin(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['target_user_id']
    inv_id = data['target_inv_id']
    price = data['target_price']
    config_text = message.text # متن کانفیگ که ادمین فرستاده

    # ۱. آپدیت وضعیت فاکتور و ذخیره کانفیگ در دیتابیس
    await invoices_col.update_one(
        {"inv_id": inv_id},
        {"$set": {"status": "✅ فعال", "config_data": config_text}}
    )

    # ۲. شارژ کیف پول کاربر
    await users_col.update_one({"user_id": user_id}, {"$inc": {"wallet": price}})

    # ۳. پیام تایید برای کاربر
    await bot.send_message(
        user_id, 
        f"✅ **اشتراک شما فعال شد!**\n\n💰 مبلغ {price:,} تومان به حساب شما منظور شد.\n🚀 هم‌اکنون می‌توانید از منوی **«اشتراک‌های من»** کانفیگ خود را دریافت کنید."
    )

    await message.answer("🚀 عالی شد! کانفیگ ثبت شد و اشتراک کاربر فعال گردید.")
    await state.finish() # خروج از وضعیت انتظار

# --- هندلر سراسری بازگشت به منوی اصلی ---
@dp.callback_query_handler(lambda c: c.data == "main_menu", state="*")
async def back_to_main_handler(callback: types.CallbackQuery, state: FSMContext):
    # ۱. تمام وضعیت‌های قبلی (مثل وسط خرید بودن) رو پاک می‌کنه
    await state.finish()
    
    # ۲. متن پیام رو به منوی اصلی تغییر میده
    try:
        await callback.message.edit_text(
            "✨ به منوی اصلی خوش آمدید\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:", 
            reply_markup=nav.main_menu()
        )
    except:
        # اگر پیام تکراری بود و ادیت نشد، فقط انسر میده
        pass
        
    # ۳. ساعتِ شنیِ روی دکمه رو حذف می‌کنه
    await callback.answer()

# ۱. منوی انتخاب نوع تست
@dp.callback_query_handler(lambda c: c.data == "get_test", state="*")
async def get_test_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎁 **بخش دریافت اشتراک تست**\nلطفاً نوع اشتراک تست خود را انتخاب کنید:",
        reply_markup=nav.test_subs_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ۲. بخش V2ray تست (رایگان با محدودیت)
@dp.callback_query_handler(lambda c: c.data == "test_v2ray", state="*")
async def test_v2ray_info(callback: types.CallbackQuery):
    text = (
        "⚠️ **قوانین اشتراک تست V2ray**\n\n"
        "هر کاربر در هر ماه فقط یک بار می‌تواند از اشتراک تست استفاده کند.\n"
        "آیا مایل به دریافت هستید؟"
    )
    await callback.message.edit_text(text, reply_markup=nav.v2ray_test_confirm(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "confirm_v2ray_test", state="*")
async def confirm_v2ray_test(callback: types.CallbackQuery):
    # ارسال پیام به کاربر
    await callback.message.edit_text(
        "✅ درخواست شما در دست بررسی است و نتیجه به زودی به شما اعلام خواهد شد.",
        reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu"))
    )
    
    # اطلاع‌رسانی به ادمین
    await bot.send_message(
        ADMIN_ID, 
        f"🆘 **درخواست اشتراک تست V2ray**\n👤 کاربر: `{callback.from_user.id}`\nنام: {callback.from_user.full_name}"
    )
    await callback.answer()

# ۳. بخش Biubiu تست (پولی - متصل به چرخه خرید)
@dp.callback_query_handler(lambda c: c.data == "test_biubiu", state="*")
async def test_biubiu_info(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🛒 **اشتراک تست Biubiu**\nلطفاً پلن تست را انتخاب کنید:",
        reply_markup=nav.biubiu_test_menu()
    )
    await callback.answer()

# نکته: دکمه Biubiu به دلیل اینکه با "plan_" شروع می‌شود، 
# خودکار وارد هندلر ask_username و پروسه پرداخت کارت/کیف پول که قبلاً نوشتیم می‌شود.

# نمایش لیست اشتراک‌های فعال
@dp.callback_query_handler(lambda c: c.data == "my_subs", state="*")
async def my_subs_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    # جستجو در کالکشن اینویس‌ها برای موارد فعال
    active_subs = await invoices_col.find({"user_id": user_id, "status": "✅ فعال"}).to_list(length=50)
    
    if not active_subs:
        await callback.answer("❌ شما در حال حاضر هیچ اشتراک فعالی ندارید.", show_alert=True)
        return

    kb = types.InlineKeyboardMarkup(row_width=1)
    for sub in active_subs:
        # نام دکمه برابر با نام پلن خریداری شده
        kb.add(types.InlineKeyboardButton(f"📦 {sub['plan']}", callback_data=f"show_cfg_{sub['inv_id']}"))
    
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu"))
    
    await callback.message.edit_text(
        "📜 **لیست اشتراک‌های فعال شما**\nبرای مشاهده جزئیات اتصال، یکی را انتخاب کنید:",
        reply_markup=kb, parse_mode="Markdown"
    )

# نمایش تاریخچه فاکتورها
@dp.callback_query_handler(lambda c: c.data == "my_invs", state="*")
async def my_invoices_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    # گرفتن ۱۰ فاکتور آخر کاربر
    all_invs = await invoices_col.find({"user_id": user_id}).sort("_id", -1).to_list(length=10)
    
    if not all_invs:
        await callback.answer("❓ شما هنوز هیچ فاکتوری ثبت نکرده‌اید.", show_alert=True)
        return

    text = "🧾 **تاریخچه فاکتورهای شما**\n\n"
    kb = types.InlineKeyboardMarkup(row_width=1)
    
    for inv in all_invs:
        status = inv['status']
        text += f"🔹 پلن: `{inv['plan']}`\n💰 مبلغ: {inv['amount']:,} تومان\n📊 وضعیت: {status}\n🗓 تاریخ: {inv['date']}\n\n"
        
        # اگر فاکتور پرداخت نشده بود، دکمه پرداخت مجدد ظاهر شود
        if "انتظار" in status:
            kb.add(types.InlineKeyboardButton(f"💳 پرداخت فاکتور {inv['plan']}", callback_data=f"repay_{inv['inv_id']}"))

    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu"))
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# هندلر پرداخت مجدد (اتصال به منوی پرداخت)
@dp.callback_query_handler(lambda c: c.data.startswith("repay_"), state="*")
async def repay_invoice_handler(callback: types.CallbackQuery, state: FSMContext):
    inv_id = callback.data.split("_")[1]
    inv = await invoices_col.find_one({"inv_id": inv_id})
    
    # ذخیره اطلاعات فاکتور در State برای ادامه پروسه خرید
    await state.update_data(price=inv['amount'], plan_name=inv['plan'], s_type=inv['type'], username=inv['username'])
    
    await callback.message.edit_text(
        f"♻️ **بازآوری فاکتور جهت پرداخت**\nمبلغ: {inv['amount']:,} تومان\nپلن: {inv['plan']}\n\nلطفاً روش پرداخت را انتخاب کنید:",
        reply_markup=nav.payment_methods(inv_id) # اینجا inv_id برای کارت به کارت استفاده می‌شود
    )


# نمایش جزئیات کانفیگ (وقتی روی دکمه اشتراک کلیک شد)
@dp.callback_query_handler(lambda c: c.data.startswith("show_cfg_"), state="*")
async def show_config_details(callback: types.CallbackQuery):
    inv_id = callback.data.split("_")[2]
    sub = await invoices_col.find_one({"inv_id": inv_id})
    
    text = (
        f"🚀 **جزئیات اشتراک: {sub['plan']}**\n\n"
        f"👤 نام کاربری: `{sub['username']}`\n"
        f"📅 تاریخ ثبت: `{sub['date']}`\n\n"
        f"🔌 **لینک اتصال (کانفیگ):**\n"
        f"`{sub.get('config_data', 'در حال آماده‌سازی...')}`"
    )
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="my_subs"))
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# ورود به پنل ادمین
@dp.callback_query_handler(lambda c: c.data == "admin_main_panel", user_id=ADMIN_ID)
async def admin_panel_main(callback: types.CallbackQuery):
    await callback.message.edit_text("🛠 به پنل مدیریت خوش آمدید.\nیکی از بخش‌ها را انتخاب کنید:", reply_markup=nav.admin_panel())

# آمار کاربران
@dp.callback_query_handler(lambda c: c.data == "admin_stats", user_id=ADMIN_ID)
async def admin_stats(callback: types.CallbackQuery):
    count = await users_col.count_documents({})
    total_invoices = await invoices_col.count_documents({})
    await callback.message.edit_text(
        f"📊 **آمار ربات:**\n\n"
        f"👥 تعداد کل کاربران: {count}\n"
        f"🧾 تعداد کل فاکتورها: {total_invoices}",
        reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="admin_main_panel"))
    )
