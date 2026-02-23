import random, string, datetime
import os
import re
import aiohttp
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from loader import dp, bot, ADMIN_ID
from database import users_col, invoices_col, plans_col, get_user, is_duplicate_receipt, save_receipt, add_invoice
import markups as nav
import config
from bson import ObjectId

async def get_marzban_token():
    payload = {
        'username': config.MARZBAN_USER, 
        'password': config.MARZBAN_PASS
    }
    async with aiohttp.ClientSession() as session:
        try:
            # ارسال درخواست برای دریافت توکن مدیریت از پنل
            async with session.post(f"{config.PANEL_URL}/api/admin/token", data=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['access_token']
                return None
        except Exception as e:
            print(f"Error getting token: {e}")
            return None

# حالا بقیه کدها که فرستادی شروع می‌شوند:
# async def create_marzban_user...

# --- توابع اصلی متصل به پنل مرزبان ---

async def create_marzban_user(username, data_gb):
    token = await get_marzban_token()
    if not token: return None
    
    headers = {"Authorization": f"Bearer {token}"}
    # تبدیل گیگابایت به بایت
    bytes_limit = int(data_gb) * 1024 * 1024 * 1024
    
    payload = {
        "username": username,
        "proxies": {"vless": {"flow": "xtls-rprx-vision"}, "vmess": {}},
        "inbounds": {"vless": []}, # استفاده از اینباندهای پیش‌فرض پنل
        "data_limit": bytes_limit,
        "expire": 0,
        "status": "active"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{config.PANEL_URL}/api/user", json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data['subscription_url']
            else:
                return None


async def renew_marzban_user(username, extra_gb):
    token = await get_marzban_token()
    if not token: return None
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{config.PANEL_URL}/api/user/{username}", headers=headers) as resp:
            if resp.status != 200: return None
            user_data = await resp.json()
            
        current_limit = user_data.get('data_limit', 0)
        new_limit = current_limit + (int(extra_gb) * 1024 * 1024 * 1024)
        
        payload = {"data_limit": new_limit, "status": "active"}
        async with session.put(f"{config.PANEL_URL}/api/user/{username}", json=payload, headers=headers) as resp:
            return resp.status == 200

async def get_crypto_prices():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.nobitex.ir/v2/orderbook/USDTIRT") as resp:
                data = await resp.json()
                tether_price = int(data['lastTradePrice']) / 10 
            return int(tether_price), 15000, 500000 
    except: return 70000, 15000, 500000

class BuyState(StatesGroup):
    entering_username = State()
    waiting_for_receipt = State()
    entering_custom_amount = State()

def generate_random_username():
    chars = string.ascii_lowercase + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(6))
    return f"AradVIP_{random_part}"

# --- ۱. دستور استارت و منوی اصلی ---
@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    args = message.get_args()
    referrer_id = args if args.isdigit() else None
    await get_user(message.from_user.id, referrer_id)
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
    price, target_username, plan_name = data.get('price', 0), data.get('username'), data.get('plan_name', '')

    if user.get('wallet', 0) >= price:
        # استخراج حجم از نام پلن (مثلاً 50GB -> 50)
        gb_match = re.findall(r'\d+', plan_name)
        gb_amount = int(gb_match[0]) if gb_match else 10
        
        # ساخت اکانت در مرزبان
        sub_link = await create_marzban_user(target_username, gb_amount)

        if sub_link:
            # کسر از موجودی و ثبت فاکتور
            await users_col.update_one({"user_id": callback.from_user.id}, {"$inc": {"wallet": -price}})
            inv_id = os.urandom(4).hex()
            buy_date = datetime.datetime.now().strftime("%Y/%m/%d")
            
            await invoices_col.insert_one({
                "inv_id": inv_id, "user_id": callback.from_user.id, "status": "✅ فعال",
                "amount": price, "plan": plan_name, "username": target_username,
                "config_data": sub_link, "date": buy_date
            })

            # تولید QR Code
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={sub_link}"

            # قالب پیام مشابه عکس ارسالی شما
            caption = (
                f"📊 **جزئیات اشتراک:**\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🟢 وضعیت: **فعال**\n"
                f"👤 نام کاربری: `{target_username}`\n"
                f"📦 پلن: `{plan_name}`\n"
                f"📅 تاریخ خرید: `{buy_date}`\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🔗 **لینک اشتراک:**\n"
                f"`{sub_link}`\n\n"
                f"🚀 خرید موفقیت‌آمیز بود. برای اتصال از QR Code یا لینک بالا استفاده کنید."
            )

            await bot.send_photo(
                callback.from_user.id, 
                photo=qr_url, 
                caption=caption, 
                parse_mode="Markdown",
                reply_markup=nav.main_menu()
            )
            await callback.message.delete()
            await state.finish()
        else:
            await callback.answer("❌ خطا در اتصال به پنل مرزبان!", show_alert=True)
    else:
        await callback.answer("❌ موجودی کافی نیست! لطفاً حساب خود را شارژ کنید.", show_alert=True)


# نمایش جزئیات کانفیگ و دکمه تمدید
@dp.callback_query_handler(lambda c: c.data.startswith("show_cfg_"), state="*")
async def show_config_details(callback: types.CallbackQuery):
    inv_id = callback.data.split("_")[2]
    sub = await invoices_col.find_one({"inv_id": inv_id})

    if not sub:
        return await callback.answer("❌ اطلاعات اشتراک یافت نشد.")

    # تولید عکس QR Code
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={sub['config_data']}"
    
    caption = (
        f"📊 **جزئیات اشتراک:**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🟢 وضعیت: **فعال**\n"
        f"👤 نام کاربری: `{sub['username']}`\n"
        f"📦 پلن: `{sub['plan']}`\n"
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
        reply_markup=nav.sub_details_menu(inv_id) # دکمه بازگشت و تمدید
    )
    await callback.message.delete()
    await callback.answer()

# --- ۷. مشاهده اشتراک‌ها و شارژ فقط با کریپتو ---
@dp.callback_query_handler(lambda c: c.data == "my_subs", state="*")
async def my_subs_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    active_subs = await invoices_col.find({"user_id": user_id, "status": "✅ فعال"}).to_list(length=50)
    if not active_subs:
        return await callback.answer("❌ شما هیچ اشتراک فعالی ندارید.", show_alert=True)

    kb = types.InlineKeyboardMarkup(row_width=1)
    for sub in active_subs:
        kb.add(types.InlineKeyboardButton(f"📦 {sub['plan']}", callback_data=f"show_cfg_{sub['inv_id']}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu"))
    await callback.message.edit_text("📜 لیست اشتراک‌های شما:", reply_markup=kb)

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
