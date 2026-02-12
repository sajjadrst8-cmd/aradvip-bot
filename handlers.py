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

# --- 1. دستور استارت ---
@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message):
    await get_user(message.from_user.id)
    await message.answer("✨ به ربات آراد VIP خوش آمدید\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=nav.main_menu())

# --- 2. بخش حساب کاربری (اصلاح شده و فعال) ---
@dp.callback_query_handler(lambda c: c.data == "my_account", state="*")
async def my_account(callback: types.CallbackQuery):
    user = await users_col.find_one({"user_id": callback.from_user.id})
    wallet_balance = user.get('wallet', 0)
    text = (
        f"👤 **Your Account Info**\n\n"
        f"🆔 User ID: `{callback.from_user.id}`\n"
        f"💰 Wallet Balance: {wallet_balance:,} Tomans\n"
        f"🎁 Referrals: {user.get('ref_count', 0)} users"
    )
    # نمایش موجودی و دکمه بازگشت
    await callback.message.edit_text(text, reply_markup=nav.main_menu(), parse_mode="Markdown")

# --- 3. لیست تعرفه‌ها (اعداد انگلیسی و چیدمان درست) ---
@dp.callback_query_handler(lambda c: c.data == "buy_new")
async def buy_start(callback: types.CallbackQuery):
    await callback.message.edit_text("Please choose your service type:", reply_markup=nav.buy_menu())

@dp.callback_query_handler(lambda c: c.data == "buy_v2ray")
async def v2ray_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    plans = [
        ("5GB - 100,000 T", 100000, "5GB"),
        ("10GB - 100,000 T", 100000, "10GB"),
        ("20GB - 100,000 T", 100000, "20GB"),
        ("30GB - 100,000 T", 100000, "30GB"),
        ("50GB - 100,000 T", 100000, "50GB"),
        ("100GB - 100,000 T", 100000, "100GB"),
        ("200GB - 100,000 T", 100000, "200GB"),
        ("300GB - 100,000 T", 100000, "300GB"),
    ]
    for text, price, name in plans:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"plan_v2ray_{price}_{name}"))
    kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="buy_new"))
    await callback.message.edit_text("🛒 V2ray Plans (Unlimited Time):", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "buy_biubiu")
async def biubiu_menu(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("👤 1 User", callback_data="biu_1"),
           types.InlineKeyboardButton("👥 2 Users", callback_data="biu_2"))
    kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="buy_new"))
    await callback.message.edit_text("Select Biubiu Subscription Type:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("biu_"))
async def biubiu_plans(callback: types.CallbackQuery):
    mode = callback.data.split("_")[1]
    kb = types.InlineKeyboardMarkup(row_width=1)
    if mode == "1":
        plans = [("1 Month - 100,000 T", 100000, "B1-1M"), ("2 Months - 200,000 T", 200000, "B1-2M"), ("3 Months - 300,000 T", 300000, "B1-3M")]
    else:
        # اضافه شدن پلن 6 ماهه طبق درخواست شما
        plans = [("1 Month - 300,000 T", 300000, "B2-1M"), ("3 Months - 600,000 T", 600000, "B2-3M"), ("6 Months - 1,100,000 T", 1100000, "B2-6M"), ("12 Months - 1,800,000 T", 1800000, "B2-12M")]
    
    for text, price, name in plans:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"plan_biu_{price}_{name}"))
    kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="buy_biubiu"))
    await callback.message.edit_text("🛒 Choose your Biubiu Plan:", reply_markup=kb)

# --- 4. ثبت فاکتور و نام کاربری ---
@dp.callback_query_handler(lambda c: c.data.startswith("plan_"), state="*")
async def ask_username(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    await state.update_data(price=int(parts[2]), plan_name=parts[3], s_type=parts[1])
    await BuyState.entering_username.set()
    await callback.message.answer("👤 Please send an English username for your account:")

@dp.message_handler(state=BuyState.entering_username)
async def create_invoice(message: types.Message, state: FSMContext):
    username = message.text.strip().lower()
    data = await state.get_data()
    inv = await add_invoice(message.from_user.id, {'price': data['price'], 'plan': data['plan_name'], 'type': data['s_type'], 'username': username})
    
    text = (
        f"🧾 **Order Invoice**\n\n"
        f"🔹 Service: {data['s_type'].upper()}\n"
        f"📦 Plan: {data['plan_name']}\n"
        f"👤 User: `{username}`\n"
        f"💰 Total: **{data['price']:,} Tomans**\n\n"
        f"Please select your payment method:"
    )
    kb = types.InlineKeyboardMarkup(row_width=2).add(
        types.InlineKeyboardButton("💳 Card to Card", callback_data=f"pay_card_{inv['inv_id']}"),
        types.InlineKeyboardButton("💰 Wallet Balance", callback_data=f"pay_wallet_{inv['inv_id']}")
    )
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

# --- 5. فرآیند پرداخت کارت به کارت ---
@dp.callback_query_handler(lambda c: c.data.startswith("pay_card_"), state="*")
async def card_payment(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    price = data.get('price', 0)
    await BuyState.waiting_for_receipt.set()
    
    text = (
        f"📌 **Payment Instructions**\n\n"
        f"Please transfer the exact amount to:\n\n"
        f"💳 Card Number: `5057851560122222`\n"
        f"👤 Name: **Sajjad Rastegaran**\n"
        f"💰 Amount: **{price:,} Tomans**\n\n"
        f"📸 Send the receipt photo here after transfer."
    )
    await callback.message.answer(text, parse_mode="Markdown")

@dp.message_handler(content_types=['photo'], state=BuyState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.answer("✅ Receipt received. Waiting for Admin approval.")
    
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✅ Approve & Send Account", callback_data=f"admin_ok_{message.from_user.id}_{data['price']}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"admin_no_{message.from_user.id}_0")
    )
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"💰 New Receipt\n👤 User: `{message.from_user.id}`\n💵 Amount: {data['price']:,}\n📦 Plan: {data['plan_name']}\n👤 Username: {data.get('username')}", 
                         reply_markup=kb, parse_mode="Markdown")
    await state.finish()

# --- 6. فرآیند پرداخت با کیف پول (مستقیم) ---
@dp.callback_query_handler(lambda c: c.data.startswith("pay_wallet_"), state="*")
async def wallet_payment(callback: types.CallbackQuery, state: FSMContext):
    user = await users_col.find_one({"user_id": callback.from_user.id})
    data = await state.get_data()
    price = data.get('price', 0)
    
    if user.get('wallet', 0) >= price:
        # کسر موجودی
        await users_col.update_one({"user_id": callback.from_user.id}, {"$inc": {"wallet": -price}})
        # اطلاع‌رسانی به ادمین برای ارسال اکانت
        await bot.send_message(ADMIN_ID, f"🔔 **خرید جدید با کیف پول**\n👤 کاربر: `{callback.from_user.id}`\n📦 پلن: {data['plan_name']}\n👤 یوزرنیم: {data.get('username')}\n\nلطفاً اکانت را برای کاربر ارسال کنید.")
        await callback.message.edit_text("✅ Payment Successful! Your order has been sent to support. You will receive your account shortly.")
        await state.finish()
    else:
        await callback.answer("❌ Insufficient Balance! Please charge your wallet first.", show_alert=True)

# --- 7. تایید ادمین (ارسال پیام نهایی) ---
@dp.callback_query_handler(lambda c: c.data.startswith("admin_"), state="*")
async def admin_verify(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    status, uid, amt = parts[1], int(parts[2]), float(parts[3])

    if status == "ok":
        # اگر کاربر در مرحله شارژ کیف پول بود، حسابش شارژ می‌شود
        # اما اگر در مرحله خرید بود، ادمین بعد از زدن این دکمه باید اکانت را بفرستد
        await users_col.update_one({"user_id": uid}, {"$inc": {"wallet": amt}})
        await bot.send_message(uid, f"✅ Receipt Approved!\n{amt:,} Tomans added to your balance. Your service will be sent shortly.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ Approved.")
    else:
        await bot.send_message(uid, "❌ Receipt Rejected. Contact support.")
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ Rejected.")
    await callback.answer()
