from aiogram import types
from aiogram.dispatcher import FSMContext
from loader import dp, bot
import config
import markups as nav
import random
import string
from states import BuyState

# --- ۱. نمایش لیست پلن‌های V2ray ---
@dp.callback_query_handler(lambda c: c.data == "buy_v2ray")
async def v2ray_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for text, price, name in config.V2RAY_PLANS: #
        kb.add(types.InlineKeyboardButton(text, callback_data=f"plan_v2ray_{price}_{name}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new"))
    await callback.message.edit_text("💎 لیست پلن‌های V2ray (حجمی):", reply_markup=kb)

# --- ۲. نمایش لیست پلن‌های BiuBiu (تک کاربره) ---
@dp.callback_query_handler(lambda c: c.data == "buy_biubiu_1u")
async def biubiu_1u_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for text, price, name in config.BIUBIU_1U_PLANS: #
        kb.add(types.InlineKeyboardButton(text, callback_data=f"biubiu_pay_{price}_{name}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new"))
    await callback.message.edit_text("👤 پلن‌های BiuBiu (تک کاربره):", reply_markup=kb)

# --- ۳. نمایش لیست پلن‌های BiuBiu (دو کاربره) ---
@dp.callback_query_handler(lambda c: c.data == "buy_biubiu_2u")
async def biubiu_2u_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for text, price, name in config.BIUBIU_2U_PLANS: #
        kb.add(types.InlineKeyboardButton(text, callback_data=f"biubiu_pay_{price}_{name}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new"))
    await callback.message.edit_text("👥 پلن‌های BiuBiu (دو کاربره):", reply_markup=kb)

# --- ۴. شروع فرآیند خرید V2ray (درخواست یوزرنیم) ---
@dp.callback_query_handler(lambda c: c.data.startswith("plan_v2ray_"), state="*")
async def ask_v2ray_username(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_") #
    price = int(parts[2])
    plan_name = parts[3]
    
    await state.update_data(s_type="v2ray", price=price, plan_name=plan_name)
    await BuyState.entering_username.set() #
    
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🎲 نام تصادفی", callback_data="random_name") #
    )
    await callback.message.edit_text(
        f"🔹 پلن انتخاب شده: {plan_name}\n"
        f"💰 قیمت: {price:,} تومان\n\n"
        f"لطفاً یک یوزرنیم انگلیسی وارد کنید یا دکمه نام تصادفی را بزنید:",
        reply_markup=kb
    )

# --- ۵. شروع فرآیند خرید BiuBiu (مستقیم به واریز) ---
@dp.callback_query_handler(lambda c: c.data.startswith("biubiu_pay_"), state="*")
async def biubiu_pay_direct(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    price = int(parts[2])
    plan_name = parts[3]
    
    await state.update_data(s_type="biubiu", price=price, plan_name=plan_name)
    await BuyState.waiting_for_receipt.set() #
    
    await callback.message.edit_text(
        f"🔹 پلن BiuBiu انتخاب شده: {plan_name}\n"
        f"💰 مبلغ قابل پرداخت: {price:,} تومان\n\n"
        f"لطفاً تصویر رسید واریز خود را ارسال کنید."
    )

# --- ۶. هندلر نام تصادفی ---
@dp.callback_query_handler(lambda c: c.data == "random_name", state=BuyState.entering_username)
async def set_random_name(callback: types.CallbackQuery, state: FSMContext):
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    username = f"Aradvip_{random_str}"
    
    await state.update_data(chosen_v2ray_username=username)
    await BuyState.waiting_for_receipt.set()
    
    data = await state.get_data()
    await callback.message.edit_text(
        f"✅ نام کاربری انتخاب شد: `{username}`\n"
        f"💰 مبلغ واریزی: {data.get('price'):,} تومان\n\n"
        f"لطفاً تصویر رسید واریز خود را ارسال کنید:",
        parse_mode="Markdown"
    )
