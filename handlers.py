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

def generate_random_username():
    chars = string.ascii_lowercase + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(6))
    return f"AradVIP_{random_part}"

# --- ۱. دستور استارت ---
@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    await get_user(message.from_user.id)
    await message.answer("✨ به ربات آراد VIP خوش آمدید\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=nav.main_menu())

# --- ۲. منوی اصلی و حساب کاربری ---
@dp.callback_query_handler(lambda c: c.data == "main_menu", state="*")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text("✨ به منوی اصلی خوش آمدید:", reply_markup=nav.main_menu())

@dp.callback_query_handler(lambda c: c.data == "my_account", state="*")
async def my_account_handler(callback: types.CallbackQuery):
    user = await users_col.find_one({"user_id": callback.from_user.id})
    wallet = user.get('wallet', 0)
    text = (
        f"👤 **اطلاعات حساب شما**\n\n"
        f"💰 موجودی: {wallet:,} تومان\n"
        f"🎁 زیرمجموعه: {user.get('ref_count', 0)} نفر"
    )
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu"))
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data == "buy_new", state="*")
async def buy_new_handler(callback: types.CallbackQuery):
    await callback.message.edit_text("لطفاً نوع سرویس مورد نظر خود را انتخاب کنید:", reply_markup=nav.buy_menu())

# --- ۳. بخش V2ray ---
@dp.callback_query_handler(lambda c: c.data == "buy_v2ray")
async def v2ray_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for text, price, name in config.V2RAY_PLANS:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"plan_v2ray_{price}_{name}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new"))
    await callback.message.edit_text("🛒 لیست پلن‌های V2ray:", reply_markup=kb)

# --- ۴. بخش Biubiu ---
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

# --- ۵. دریافت نام کاربری و صدور فاکتور ---

async def proceed_to_invoice(message: types.Message, state: FSMContext, username: str):
    data = await state.get_data()
    price = data.get('price')
    s_type = data.get('s_type')
    plan_name = data.get('plan_name')

    display_plan = plan_name
    if s_type == "biu":
        parts = plan_name.split('-')
        users = "1u" if "1" in parts[0] else "2u"
        display_plan = f"BiuBiu_{parts[1].lower()}{users}"
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

# --- ۶. فرآیند پرداخت و رسید ---
@dp.callback_query_handler(lambda c: c.data.startswith("pay_card_"), state="*")
async def card_payment(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await BuyState.waiting_for_receipt.set()
    text = (
        f"📌 **راهنمای واریز**\n\n"
        f"مبلغ **{data['price']:,} تومان** را واریز کنید:\n"
        f"💳 شماره کارت: `{config.CARD_NUMBER}`\n"
        f"👤 بنام: **{config.CARD_NAME}**\n\n"
        f"📸 رسید را اینجا ارسال کنید."
    )
    await callback.message.answer(text, parse_mode="Markdown")

@dp.message_handler(content_types=['photo'], state=BuyState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await message.answer("✅ رسید دریافت شد. منتظر تایید مدیریت بمانید.")
    
    # اصلاح بخش کپشن برای جلوگیری از خطای Markdown
    username = str(data.get('username', 'نامشخص')).replace("_", "\\_") # خنثی کردن کاراکتر زیرخط
    
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✅ تایید", callback_data=f"admin_ok_{message.from_user.id}_{data['price']}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"admin_no_{message.from_user.id}_0")
    )
    
    caption_text = (
        f"💰 **رسید جدید**\n\n"
        f"👤 کاربر: `{message.from_user.id}`\n"
        f"💵 مبلغ: {data['price']:,} تومان\n"
        f"📦 پلن: {data.get('plan_name')}\n"
        f"👤 یوزرنیم: `{username}`"
    )
    
    try:
        await bot.send_photo(
            ADMIN_ID, 
            message.photo[-1].file_id, 
            caption=caption_text, 
            reply_markup=kb, 
            parse_mode="Markdown"
        )
    except Exception as e:
        # اگر باز هم خطا داد، بدون مارک‌داون بفرست که ربات کرش نکنه
        await bot.send_photo(
            ADMIN_ID, 
            message.photo[-1].file_id, 
            caption=caption_text.replace("*", "").replace("`", ""), 
            reply_markup=kb
        )
        
    await state.finish()
    else:
        await callback.answer("❌ موجودی کافی نیست!", show_alert=True)

# --- ۷. بخش مدیریت (تایید/رد رسید) ---

@dp.callback_query_handler(lambda c: c.data.startswith("admin_"), state="*")
async def admin_decision_handler(callback: types.CallbackQuery):
    # فرمت دیتا: admin_ok_USERID_PRICE یا admin_no_USERID_0
    parts = callback.data.split("_")
    action = parts[1]
    user_id = int(parts[2])
    price = int(parts[3])

    if action == "ok":
        # ۱. اطلاع‌رسانی به کاربر
        try:
            success_text = (
                "✅ **رسید شما توسط مدیریت تایید شد!**\n\n"
                "سفارش شما در حال آماده‌سازی است و به زودی ارسال می‌شود.\n"
                "از اعتماد شما سپاسگزاریم. 🙏"
            )
            await bot.send_message(user_id, success_text, parse_mode="Markdown")
            
            # ۲. بروزرسانی پیام ادمین (برای اینکه دکمه‌ها غیب شوند)
            await callback.message.edit_caption(
                caption=callback.message.caption + "\n\n✅ **تایید و ارسال شد.**",
                reply_markup=None # حذف دکمه‌ها
            )
            await callback.answer("تایید شد و به کاربر اطلاع داده شد.", show_alert=True)
            
        except Exception as e:
            await callback.answer(f"خطا در اطلاع‌رسانی به کاربر: {e}", show_alert=True)

    elif action == "no":
        # ۱. اطلاع‌رسانی به کاربر
        try:
            fail_text = (
                "❌ **متأسفانه رسید شما توسط مدیریت رد شد.**\n\n"
                "علت احتمالی: تصویر ناخوانا، مبلغ اشتباه یا عدم واریز.\n"
                "لطفاً در صورت بروز مشکل با پشتیبانی در ارتباط باشید."
            )
            await bot.send_message(user_id, fail_text, parse_mode="Markdown")
            
            # ۲. بروزرسانی پیام ادمین
            await callback.message.edit_caption(
                caption=callback.message.caption + "\n\n❌ **رد شد.**",
                reply_markup=None
            )
            await callback.answer("رسید رد شد.", show_alert=True)
            
        except Exception as e:
            await callback.answer(f"خطا: {e}", show_alert=True)
