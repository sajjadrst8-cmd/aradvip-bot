import random, string, datetime
import os
import re
import aiohttp
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
class BuyState(StatesGroup):
    choosing_plan = State()
    entering_username = State()
    waiting_for_receipt = State()
class AdminState(StatesGroup):
    waiting_for_broadcast_msg = State()
    waiting_for_user_search = State()

from loader import dp, bot, ADMIN_ID
from database import users_col, invoices_col, plans_col, get_user, is_duplicate_receipt, save_receipt, add_invoice
import markups as nav
import config
from bson import ObjectId



# --- ۱. دستور استارت و منوی اصلی ---
@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    
    # چک کردن اینکه آیا کاربر قبلاً ثبت‌نام کرده (شماره‌اش در دیتابیس هست؟)
    user = await users_col.find_one({"user_id": user_id})
    
    if user and user.get("phone"):
        # اگر ثبت نام شده بود، منوی اصلی را بفرست
        await message.answer(
            f"سلام {message.from_user.full_name} عزیز، به ربات آراد VIP خوش آمدید!",
            reply_markup=nav.main_menu(user_id)
        )
    else:
        # اگر ثبت نام نشده بود، درخواست شماره کن
        await message.answer(
            "⚠️ برای استفاده از خدمات ربات، ابتدا باید ثبت‌نام کنید.\n\n"
            "لطفاً با استفاده از دکمه زیر شماره موبایل خود را ارسال کنید 👇",
            reply_markup=nav.register_menu()
        )


@dp.message_handler(content_types=types.ContentType.CONTACT)
async def get_contact(message: types.Message):
    contact = message.contact
    user_id = message.from_user.id
    
    # چک کردن اینکه آیا شماره متعلق به خود کاربر است (برای امنیت)
    if contact.user_id != user_id:
        return await message.answer("❌ لطفاً شماره موبایل خودتان را ارسال کنید.")

    # ذخیره شماره در دیتابیس (آپدیت یا اینسرت)
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {
            "phone": contact.phone_number,
            "username": message.from_user.username,
            "full_name": message.from_user.full_name,
            "join_date": datetime.datetime.now().strftime("%Y/%m/%d")
        }},
        upsert=True
    )

    # حذف دکمه شماره موبایل و ارسال پیام موفقیت
    await message.answer(
        "✅ ثبت‌نام شما با موفقیت انجام شد!\n\n"
        "حالا برای ورود به پنل کاربری، دستور /start را مجدداً ارسال یا لمس کنید.",
        reply_markup=types.ReplyKeyboardRemove()
    )

# --- هندلر ورود به منوی انتخاب نوع تست ---
@dp.callback_query_handler(lambda c: c.data == 'get_test', state="*")
async def get_test_menu_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎁 **بخش دریافت اشتراک تست رایگان**\n\n"
        "لطفاً یکی از سرویس‌های زیر را برای دریافت اکانت تست انتخاب کنید:\n"
        "⚠️ هر کاربر فقط یک‌بار می‌تواند تست دریافت کند.",
        reply_markup=nav.test_subs_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

# --- هندلر دکمه تست V2ray ---
from datetime import datetime, timedelta

# این هندلر وقتی کاربر روی "تایید نهایی تست" کلیک می‌کند اجرا می‌شود
# این هندلر را قبل از process_test_v2ray_final اضافه کن
@dp.callback_query_handler(lambda c: c.data == 'test_v2ray', state="*")
async def ask_v2ray_test_confirmation(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🚀 **درخواست اشتراک تست V2ray**\n\n"
        "این اشتراک ۲۰۰ مگابایت حجم دارد و به مدت ۲۴ ساعت معتبر است.\n"
        "آیا مایل به دریافت هستید؟",
        reply_markup=nav.v2ray_test_confirm(), # این همان تابعی است که دکمه confirm_v2ray_test را دارد
        parse_mode="Markdown"
    )
    await callback.answer()

async def process_test_v2ray_final(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # ۱. بررسی محدودیت ۳ ماهه (۹۰ روز)
    # فرض بر این است که تاریخ آخرین تست را در دیتابیس در فیلد last_test_date ذخیره می‌کنیم
    user_data = await db.users.find_one({"user_id": user_id}) # نام کالکشن دیتابیس خودت را چک کن
    
    if user_data and "last_test_date" in user_data:
        last_test = user_data["last_test_date"]
        if datetime.now() < last_test + timedelta(days=90):
            days_left = (last_test + timedelta(days=90) - datetime.now()).days
            await callback.answer(f"❌ شما قبلاً تست گرفته‌اید. {days_left} روز دیگر می‌توانید مجدداً تست بگیرید.", show_alert=True)
            return

    await callback.message.edit_text("⏳ در حال ساخت اکانت ۲۰۰ مگابایتی در پنل مرزبان...")

    # ۲. فراخوانی تابع ساخت اکانت مرزبان که قبلاً نوشتیم
    # فقط مقدار حجم را روی 200 * 1024 * 1024 (معادل ۲۰۰ مگابایت به بایت) تنظیم می‌کنیم
    test_volume = 200 * 1024 * 1024 
    
    try:
        # نام این تابع (add_user_marzban) را مطابق با چیزی که قبلاً در کدت داشتی چک کن
        response = await marzban_api.add_user(
            username=f"test_{user_id}",
            data_limit=test_volume,
            proxies={"vless": {}}, # یا هر پروتکلی که استفاده می‌کنی
            expire=int((datetime.now() + timedelta(days=1)).timestamp()) # انقضا ۱ روزه
        )

        if response:
            # ۳. آپدیت زمان آخرین تست در دیتابیس
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"last_test_date": datetime.now()}},
                upsert=True
            )

            await callback.message.edit_text(
                f"✅ **اشتراک تست شما با موفقیت ساخته شد!**\n\n"
                f"📊 حجم: ۲۰۰ مگابایت\n"
                f"⏱ اعتبار: ۲۴ ساعت\n\n"
                f"<code>{response['subscription_url']}</code>",
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text("❌ خطا در ساخت اکانت. دوباره تلاش کنید.")

    except Exception as e:
        print(f"Marzban Test Error: {e}")
        await callback.message.edit_text("❌ خطا در اتصال به پنل مرزبان.")
    
    await callback.answer()


# --- هندلر دکمه تست Biubiu ---
@dp.callback_query_handler(lambda c: c.data == 'test_biubiu', state="*")
async def show_biubiu_test_plans(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🛡 **انتخاب پلن تست Biubiu**\n\n"
        "لطفاً پلن مورد نظر خود را انتخاب کنید تا فاکتور صادر شود:",
        reply_markup=nav.biubiu_test_menu(), # این تابع دکمه plan_biu_50000_1DayTest را نشان می‌دهد
        parse_mode="Markdown"
    )
    await callback.answer()



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
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💰 شارژ حساب (ارز دیجیتال)", callback_data="charge_crypto"),
        types.InlineKeyboardButton("👥 زیرمجموعه‌گیری", callback_data="referral_section"),
        types.InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
    )
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data == "referral_section", state="*")
async def referral_handler(callback: types.CallbackQuery):
    bot_info = await bot.get_me()
    invite_link = f"https://t.me/{bot_info.username}?start={callback.from_user.id}"
    user = await users_col.find_one({"user_id": callback.from_user.id})
    text = (
        f"💰 **سیستم کسب درآمد**\n\n"
        f"👥 زیرمجموعه‌های شما: **{user.get('ref_count', 0)} نفر**\n"
        f"🎁 پاداش: **۱۰٪ از هر خرید**\n\n"
        f"🔗 **لینک دعوت شما:**\n`{invite_link}`"
    )
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="my_account"))
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- ۳. انتخاب سرویس و پلن ---
@dp.callback_query_handler(lambda c: c.data == "buy_new", state="*")
async def buy_new_handler(callback: types.CallbackQuery):
    await callback.message.edit_text("لطفاً نوع سرویس مورد نظر را انتخاب کنید:", reply_markup=nav.buy_menu())

@dp.callback_query_handler(lambda c: c.data == "buy_v2ray")
async def v2ray_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for text, price, name in config.V2RAY_PLANS:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"plan_v2ray_{price}_{name}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new"))
    await callback.message.edit_text("🛒 لیست پلن‌های V2ray (حجمی):", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("plan_"), state="*")
async def ask_username(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    await state.update_data(s_type=parts[1], price=int(parts[2]), plan_name=parts[3])
    await BuyState.entering_username.set()
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🎲 انتخاب نام تصادفی", callback_data="random_name"))
    await callback.message.answer("👤 یک نام کاربری (انگلیسی) ارسال کنید یا دکمه زیر را بزنید:", reply_markup=kb)

# --- ۴. صدور فاکتور و دریافت رسید ---
async def proceed_to_invoice(message: types.Message, state: FSMContext, username: str):
    data = await state.get_data()
    price, s_type, plan_name = data.get('price'), data.get('s_type'), data.get('plan_name')
    user_id = message.chat.id 

    display_plan = f"{s_type.upper()}_{plan_name}"
    inv = await add_invoice(user_id, {'price': price, 'plan': display_plan, 'type': s_type, 'username': username})

    text = (
        f"🧾 **فاکتور پرداخت آراد VIP**\n\n"
        f"📦 پلن: `{display_plan}`\n"
        f"👤 نام کاربری: `{username}`\n"
        f"💰 مبلغ: **{price:,} تومان**\n\n"
        f"👇 روش پرداخت را انتخاب کنید:"
    )
    await bot.send_message(user_id, text, reply_markup=nav.payment_methods(inv['inv_id']), parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data == "random_name", state=BuyState.entering_username)
async def handle_random_name(callback: types.CallbackQuery, state: FSMContext):
    r_name = generate_random_username()
    await state.update_data(username=r_name)
    await callback.message.delete()
    await proceed_to_invoice(callback.message, state, r_name)

@dp.message_handler(state=BuyState.entering_username)
async def handle_manual_username(message: types.Message, state: FSMContext):
    username = message.text.strip().lower()
    if not username.replace("_", "").isalnum():
        return await message.answer("❌ نام کاربری فقط شامل حروف انگلیسی و عدد باشد.")
    await state.update_data(username=username)
    await proceed_to_invoice(message, state, username)

# --- ۵. هندلر تایید/رد هوشمند ادمین (متصل به مرزبان) ---
@dp.callback_query_handler(lambda c: c.data.startswith("admin_"), user_id=ADMIN_ID, state="*")
async def admin_decision(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    action, user_id, price, purpose = parts[1], int(parts[2]), int(parts[3]), parts[4]
    
    if action == "ok":
        invoice = await invoices_col.find_one({"user_id": user_id, "status": "🟠 در انتظار"}, sort=[("_id", -1)])
        if not invoice: return await callback.answer("❌ فاکتور یافت نشد")
        
        gb = re.findall(r'\d+', invoice['plan'])[0] if re.findall(r'\d+', invoice['plan']) else 10
        
        if purpose == "buy":
            res = await create_marzban_user(invoice['username'], gb)
            if res:
                await invoices_col.update_one({"inv_id": invoice['inv_id']}, {"$set": {"status": "✅ فعال", "config_data": res}})
                await bot.send_message(user_id, f"✅ پرداخت تایید شد!\n👤 یوزر: `{invoice['username']}`\n🔗 لینک:\n`{res}`")
                await callback.message.edit_caption(caption=callback.message.caption + f"\n\n✅ اکانت {invoice['username']} ساخته شد.")
            else:
                await callback.answer("❌ خطا در مرزبان (نام تکراری؟)", show_alert=True)

        elif purpose == "charge":
            await users_col.update_one({"user_id": user_id}, {"$inc": {"wallet": price}})
            await bot.send_message(user_id, f"✅ مبلغ {price:,} تومان به کیف پول شما اضافه شد.")
            await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ کیف پول شارژ شد.")

    elif action == "no":
        await bot.send_message(user_id, "❌ رسید شما توسط مدیریت رد شد.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ رد شد.")
    await callback.answer()

# دریافت عکس رسید
@dp.message_handler(content_types=['photo'], state=BuyState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    file_unique_id = message.photo[-1].file_unique_id
    if await is_duplicate_receipt(file_unique_id):
        return await message.answer("❌ این رسید قبلاً ثبت شده است.")

    data = await state.get_data()
    amount = data.get('charge_amount') or data.get('price', 0)
    purpose = "buy" if data.get('plan_name') else "charge"
   
# --- ۶. پرداخت با کیف پول و سیستم تمدید ---
@dp.callback_query_handler(lambda c: c.data.startswith("pay_wallet_"), state="*")
async def wallet_payment(callback: types.CallbackQuery, state: FSMContext):
    user = await users_col.find_one({"user_id": callback.from_user.id})
    data = await state.get_data()
    
    price = data.get('price', 0)
    target_username = data.get('username')
    plan_name = data.get('plan_name', '')
    service_type = data.get('s_type') # این متغیر مشخص می‌کند v2ray است یا biubiu

    if user.get('wallet', 0) < price:
        return await callback.answer("❌ موجودی کافی نیست!", show_alert=True)

    # --- مسیر اول: اگر سرویس V2ray باشد (اتصال به مرزبان) ---
    if service_type == "v2ray":
        gb_match = re.findall(r'\d+', plan_name)
        gb_amount = int(gb_match[0]) if gb_match else 10
        
        sub_link = await create_marzban_user(target_username, gb_amount)
        
        if not sub_link:
            return await callback.answer("❌ خطا در اتصال به پنل مرزبان!", show_alert=True)
            
        final_link = sub_link
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={final_link}"

    # --- مسیر دوم: اگر سرویس Biubiu باشد (دریافت از دیتابیس یا متن ثابت) ---
    else:
        # اینجا می‌توانید لینک دانلود Biubiu یا کد اشتراک آن را قرار دهید
        final_link = "لینک یا کد اشتراک Biubiu شما" 
        qr_url = None # برای بیو بیو شاید QR نیاز نباشد

    # --- ثبت در دیتابیس و کسر موجودی (مشترک برای هر دو) ---
    await users_col.update_one({"user_id": callback.from_user.id}, {"$inc": {"wallet": -price}})
    inv_id = os.urandom(4).hex()
    buy_date = datetime.datetime.now().strftime("%Y/%m/%d")
    
    await invoices_col.insert_one({
        "inv_id": inv_id, "user_id": callback.from_user.id, "status": "✅ فعال",
        "amount": price, "plan": plan_name, "username": target_username,
        "config_data": final_link, "date": buy_date, "type": service_type
    })

    # ارسال خروجی به کاربر
    caption = (
        f"🛍 **خرید موفقیت‌آمیز سرویس {service_type.upper()}**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 نام کاربری: `{target_username}`\n"
        f"📦 پلن: `{plan_name}`\n"
        f"📅 تاریخ: `{buy_date}`\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔑 کد/لینک اتصال:\n`{final_link}`"
    )

    if qr_url:
        await bot.send_photo(callback.from_user.id, photo=qr_url, caption=caption, parse_mode="Markdown", reply_markup=nav.main_menu())
    else:
        await bot.send_message(callback.from_user.id, caption, parse_mode="Markdown", reply_markup=nav.main_menu())

    await callback.message.delete()
    await state.finish()



# نمایش جزئیات کانفیگ و دکمه تمدید
@dp.callback_query_handler(lambda c: c.data.startswith("show_cfg_"), state="*")
async def show_config_details(callback: types.CallbackQuery):
    inv_id = callback.data.split("_")[2]
    sub = await invoices_col.find_one({"inv_id": inv_id})

    if not sub:
        return await callback.answer("❌ اطلاعات یافت نشد.")

    # دریافت آمار مصرف (اگر v2ray است)
    used, remaining, total = "0", "نامحدود", "نامحدود"
    if sub.get('type', 'v2ray') == 'v2ray':
        usage_data = await get_marzban_user_usage(sub['username'])
        if usage_data:
            used, remaining, total = usage_data

    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={sub['config_data']}"
    
    caption = (
        f"📊 **جزئیات اشتراک:**\n"
        f"وضعیت: 🟢 فعال\n"
        f"👤 نام کاربری: `{sub['username']}`\n"
        f"📥 مصرف شده: `{used} GB`\n"
        f"📤 باقیمانده: `{remaining} GB`\n"
        f"📅 تاریخ ثبت: `{sub['date']}`\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔗 **لینک اشتراک:**\n"
        f"`{sub['config_data']}`"
    )

    await bot.send_photo(
        callback.from_user.id, 
        photo=qr_url, 
        caption=caption, 
        parse_mode="Markdown",
        reply_markup=nav.sub_details_menu(inv_id) # مطمئن شو در مارک آپ ها این تابع هست
    )
    await callback.message.delete()
    await callback.answer()



# --- ۷. مشاهده اشتراک‌ها و شارژ فقط با کریپتو ---
@dp.callback_query_handler(lambda c: c.data == "my_subs", state="*")
async def my_subs_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    active_subs = await invoices_col.find({"user_id": user_id, "status": "✅ فعال"}).to_list(length=100)
    
    if not active_subs:
        return await callback.answer("❌ شما هیچ اشتراک فعالی ندارید.", show_alert=True)
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    
    for sub in active_subs:
        # نمایش یوزرنیم به جای حجم طبق درخواست شما
        kb.add(types.InlineKeyboardButton(
            text=f"👤 اکانت: {sub['username']}", 
            callback_data=f"show_cfg_{sub['inv_id']}"
        ))
    
    kb.add(types.InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="main_menu"))
    
    try:
        await callback.message.edit_text(
            "📜 لیست اشتراک‌های شما:\n(برای مشاهده جزئیات و لینک اتصال کلیک کنید)", 
            reply_markup=kb
        )
    except:
        pass
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "charge_crypto", state="*")
async def crypto_menu_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💎 **شارژ حساب با ارز دیجیتال**\nلطفاً ارز مورد نظر خود را جهت واریز انتخاب کنید:",
        reply_markup=nav.charge_menu()
    )

@dp.callback_query_handler(lambda c: c.data.startswith("net_") or c.data in ["charge_trx", "charge_ton"], state="*")
async def crypto_final_step(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data
    prices = await get_crypto_prices() # [tether, trx, ton]
    
    if "usdt" in data:
        coin, addr, price = "Tether (TRC20)", config.WALLETS["usdt_trc20"], prices[0]
    elif "trx" in data:
        coin, addr, price = "Tron (TRX)", config.WALLETS["trx"], prices[1]
    elif "ton" in data:
        coin, addr, price = "TON Coin", config.WALLETS["ton"], prices[2]
    else: return

    await state.update_data(charge_amount=price) # قیمت برای یک واحد جهت محاسبه مدیریت
    text = (
        f"💎 **واریز {coin}**\n"
        f"✅ آدرس واریز:\n`{addr}`\n\n"
        f"📸 لطفاً پس از واریز، تصویر رسید (Hash یا اسکرین‌شات) را ارسال کنید."
    )
    await BuyState.waiting_for_receipt.set()
    await callback.message.answer(text, parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data == "main_menu", state="*")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        await callback.message.edit_text(
            "✨ منوی اصلی آراد VIP:", 
            reply_markup=nav.main_menu()
        )
    except:
        # این بخش برای جلوگیری از خطا در صورت عدم تغییر متن پیام است
        pass
    await callback.answer()


# هندلر دکمه تمدید (فرستادن کاربر برای پرداخت)
@dp.callback_query_handler(lambda c: c.data.startswith("renew_request_"), state="*")
async def renew_request_handler(callback: types.CallbackQuery, state: FSMContext):
    inv_id = callback.data.split("_")[2]
    sub = await invoices_col.find_one({"inv_id": inv_id})
    
    # ذخیره اطلاعات قبلی در استیت برای فاکتور جدید
    # مبلغ را از پلن قبلی برمی‌داریم (یا می‌توانید پلن جدید بپرسید، فعلاً طبق همان قبلی جلو می‌رود)
    await state.update_data(
        price=sub['amount'], 
        plan_name=sub['plan'], 
        s_type=sub.get('type', 'v2ray'), 
        username=sub['username'],
        purpose="renew" # مشخص می‌کنیم که این یک تمدید است
    )

    await callback.message.edit_text(
        f"♻️ **درخواست تمدید اشتراک**\n\n"
        f"👤 یوزرنیم: `{sub['username']}`\n"
        f"💰 مبلغ تمدید: **{sub['amount']:,} تومان**\n\n"
        f"لطفاً روش پرداخت را انتخاب کنید:",
        reply_markup=nav.payment_methods(inv_id)
    )

