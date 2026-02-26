from aiogram import types
from loader import dp, bot
from database import get_user
from aiogram.dispatcher import FSMContext
from states import BuyState
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import markups as nav
    
@dp.message_handler(commands=['start'], state="*")
async def start_handler(message: types.Message, state: FSMContext):
    await state.finish() # ریست کردن وضعیت کاربر
    
    user_id = message.from_user.id
    first_name = message.from_user.first_name # نام کاربر
    
    # متنی که خواسته بودی
    welcome_text = (
        f"سلام {first_name} عزیز\n"
        f"به سیستم هوشمند فروش آراد وی ای پی خوش آمدید\n"
        f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    # ارسال پیام همراه با پاس دادن user_id به کیبورد
    await message.answer(welcome_text, reply_markup=nav.main_menu(user_id))

# --- هندلر بازگشت به منوی اصلی (از همه جا) ---
@dp.callback_query_handler(lambda c: c.data == "main_menu", state="*")
async def back_to_main(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    
    user_id = call.from_user.id
    first_name = call.from_user.first_name
    
    text = (
        f"سلام {first_name}\n"
        f"به منوی اصلی بازگشتید. لطفاً انتخاب کنید:"
    )
    
    await call.message.edit_text(text, reply_markup=nav.main_menu(user_id))

# سایر هندلرهای عمومی (مثل دکمه پشتیبانی)
@dp.callback_query_handler(lambda c: c.data == "support", state="*")
async def support_handler(call: types.CallbackQuery):
    await call.message.answer("💎 برای ارتباط با پشتیبانی به آیدی @Aradvip پیام دهید.")
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == "buy_new", state="*")
async def process_buy_new(call: types.CallbackQuery):
    import markups as nav
    await call.message.edit_text(
        "🚀 لطفاً نوع سرویس مورد نظر خود را انتخاب کنید:",
        reply_markup=nav.buy_menu()
    )
    await call.answer()

# --- هندلر حساب کاربری ---
@dp.callback_query_handler(lambda c: c.data == "my_account", state="*")
async def my_account_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_data = get_user(user_id) # فرض بر اینکه این تابع در database.py وجود دارد
    
    wallet_balance = user_data[2] if user_data else 0 # دریافت موجودی از دیتابیس
    
    text = (
        f"👤 **حساب کاربری شما**\n\n"
        f"🆔 شناسه عددی: `{user_id}`\n"
        f"💰 موجودی کیف پول: {wallet_balance:,} تومان\n\n"
        f"🎁 با شارژ کیف پول می‌توانید سریع‌تر خرید کنید."
    )
    
    # استفاده از منوی شارژ که در markups تعریف کردی
    await call.message.edit_text(text, reply_markup=nav.charge_menu(), parse_mode="Markdown")
    await call.answer()

# --- هندلر اشتراک‌های من ---
@dp.callback_query_handler(lambda c: c.data == "my_subs", state="*")
async def my_subs_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    
    # پیدا کردن اشتراک‌های تایید شده کاربر از دیتابیس
    # توجه: باید مطمئن شوی موقع تایید ادمین، وضعیت اینویس به success تغییر کند
    user_subs = await invoices_col.find({"user_id": user_id, "status": "success"}).to_list(length=100)
    
    if not user_subs:
        text = "📜 **لیست اشتراک‌های فعال شما:**\n\n❌ در حال حاضر اشتراک فعالی یافت نشد."
        await call.message.edit_text(text, reply_markup=nav.main_menu(user_id), parse_mode="Markdown")
    else:
        text = "📜 **لیست اشتراک‌های شما:**\n\nبرای مشاهده جزئیات هر اشتراک روی آن کلیک کنید:"
        kb = InlineKeyboardMarkup(row_width=1)
        
        for sub in user_subs:
            # نمایش نام کاربری مرزبان روی دکمه
            username = sub.get('username', 'نامعلوم')
            kb.add(InlineKeyboardButton(f"🚀 {username}", callback_data=f"view_sub_{username}"))
            
        kb.add(InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu"))
        
        # با ارسال reply_markup جدید، دکمه‌های قبلی جایگزین می‌شوند
        await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    
    await call.answer()
# --- هندلر فاکتورهای من ---
# --- بخش نمایش لیست فاکتورها ---
@dp.callback_query_handler(lambda c: c.data == "my_invoices", state="*")
async def show_my_invoices(call: types.CallbackQuery):
    user_id = call.from_user.id
    # دریافت فاکتورها از دیتابیس
    invoices = await invoices_col.find({"user_id": user_id}).sort("date", -1).to_list(length=20)
    
    if not invoices:
        return await call.answer("❌ شما هنوز هیچ فاکتوری ندارید.", show_alert=True)
    
    text = "🧾 **لیست فاکتورهای شما:**\n\nبرای مشاهده جزئیات، روی فاکتور کلیک کنید:"
    kb = InlineKeyboardMarkup(row_width=1)
    
    for inv in invoices:
        status = inv.get('status', 'نامعلوم')
        amount = inv.get('amount', 0)
        # تعیین آیکون بر اساس وضعیت موجود در دیتابیس
        icon = "✅" if "success" in status or "پرداخت موفق" in status else "🟠" if "در انتظار" in status else "❌"
        
        btn_text = f"{icon} مبلغ: {amount:,} تومان | {inv.get('date', '')}"
        kb.add(InlineKeyboardButton(btn_text, callback_data=f"view_inv_{inv['_id']}"))
    
    kb.add(InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu"))
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- بخش نمایش جزئیات یک فاکتور خاص ---
@dp.callback_query_handler(lambda c: c.data.startswith("view_inv_"), state="*")
async def view_invoice_details(call: types.CallbackQuery):
    inv_id = call.data.split("_")[2]
    from bson import ObjectId # برای تبدیل رشته آیدی به فرمت دیتابیس
    
    inv = await invoices_col.find_one({"_id": ObjectId(inv_id)})
    if not inv:
        return await call.answer("❌ فاکتور یافت نشد.")
    
    status = inv.get('status', 'نامعلوم')
    text = (
        f"📑 **جزئیات فاکتور**\n\n"
        f"🆔 شناسه: `{inv.get('inv_id', inv_id)}`\n"
        f"💎 پلن: `{inv.get('plan', '-')}`\n"
        f"💰 مبلغ: `{inv['amount']:,} تومان`\n"
        f"📅 تاریخ: `{inv.get('date', '-')}`\n"
        f"🚦 وضعیت: {status}"
    )
    
    kb = InlineKeyboardMarkup(row_width=1)
    
    # اگر فاکتور هنوز پرداخت نشده باشد، دکمه پرداخت مجدد فعال می‌شود
    if "در انتظار" in status:
        kb.add(InlineKeyboardButton("💳 پرداخت این فاکتور", callback_data=f"repay_{inv_id}"))
    
    kb.add(InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="my_invoices"))
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# --- بخش شروع مجدد فرآیند پرداخت (Repay) ---
@dp.callback_query_handler(lambda c: c.data.startswith("repay_"), state="*")
async def repay_invoice(call: types.CallbackQuery, state: FSMContext):
    inv_id = call.data.split("_")[1]
    from bson import ObjectId
    
    inv = await invoices_col.find_one({"_id": ObjectId(inv_id)})
    if not inv: return
    
    # ذخیره اطلاعات پلن در استیت برای مراحل بعدی پرداخت
    await state.update_data(price=inv['amount'], plan_name=inv['plan'])
    
    await call.message.edit_text(
        f"💳 در حال پرداخت مجدد فاکتور به مبلغ {inv['amount']:,} تومان...\nلطفاً روش پرداخت را انتخاب کنید:",
        reply_markup=nav.payment_methods() # نمایش دکمه‌های انتخاب روش پرداخت
    )