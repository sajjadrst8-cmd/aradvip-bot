from aiogram import types
from aiogram.dispatcher import FSMContext
from loader import dp, bot, ADMIN_ID
import markups as nav
from database import invoices_col, users_col
from bson import ObjectId

# --- ورود به پنل مدیریت ---
@dp.callback_query_handler(lambda c: c.data == 'admin_panel', state="*")
async def open_admin_panel(callback: types.CallbackQuery, state: FSMContext):
    if str(callback.from_user.id) == str(ADMIN_ID):
        await state.finish()
        await callback.message.edit_text(
            "👨‍✈️ به پنل مدیریت خوش آمدید.\nلطفاً یک گزینه را انتخاب کنید:",
            reply_markup=nav.admin_panel()
        )
    else:
        await callback.answer("❌ شما دسترسی ادمین ندارید.", show_alert=True)
    await callback.answer()

# --- سیستم تایید یا رد تراکنش توسط ادمین ---
@dp.callback_query_handler(lambda c: c.data.startswith('verify_pay_'), state="*")
async def admin_approve_payment(callback: types.CallbackQuery):
    inv_id = callback.data.replace('verify_pay_', '')
    invoice = invoices_col.find_one({"_id": ObjectId(inv_id)})

    if invoice and invoice['status'] == 'pending':
        user_id = invoice['user_id']
        amount = invoice['amount']
        
        # ۱. آپدیت موجودی کاربر در دیتابیس
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": amount}})
        # ۲. تغییر وضعیت فاکتور به موفق
        invoices_col.update_one({"_id": ObjectId(inv_id)}, {"$set": {"status": "success"}})
        
        # اطلاع‌رسانی به کاربر
        try:
            await bot.send_message(user_id, f"✅ واریز شما تایید شد!\nمبلغ {amount:,} تومان به کیف پول شما اضافه شد.")
        except:
            pass
            
        await callback.message.edit_text(f"✅ رسید تایید شد.\nمبلغ {amount:,} به حساب کاربر {user_id} شارژ شد.")
    else:
        await callback.answer("این فاکتور قبلاً تعیین تکلیف شده است.")
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('reject_pay_'), state="*")
async def admin_reject_payment_start(callback: types.CallbackQuery):
    inv_id = callback.data.replace('reject_pay_', '')
    invoice = invoices_col.find_one({"_id": ObjectId(inv_id)})
    
    if invoice:
        user_id = invoice['user_id']
        await callback.message.edit_text(
            f"دلیل رد تراکنش برای کاربر {user_id} چیست؟",
            reply_markup=nav.admin_reject_reasons_menu(user_id)
        )
    await callback.answer()
