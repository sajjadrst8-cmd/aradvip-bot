from aiogram import types
from aiogram.dispatcher import FSMContext
from loader import dp, bot, ADMIN_ID
import markups as nav
from database import invoices_col, users_col
from bson import ObjectId

# استیت‌های مورد نیاز برای ادمین
from aiogram.dispatcher.filters.state import State, StatesGroup
class AdminStates(StatesGroup):
    waiting_for_manual_amount = State()
    waiting_for_broadcast_msg = State()
    waiting_for_all_charge_amount = State()

# --- ۱. مدیریت رسیدها ---
@dp.callback_query_handler(lambda c: c.data == "admin_receipts", state="*")
async def admin_receipts_main(callback: types.CallbackQuery):
    await callback.message.edit_text("📑 مدیریت رسیدهای واریزی:", reply_markup=nav.admin_receipts_menu())

@dp.callback_query_handler(lambda c: c.data == "receipts_pending", state="*")
async def list_pending_receipts(callback: types.CallbackQuery):
    pending = invoices_col.find({"status": "pending"})
    kb = InlineKeyboardMarkup(row_width=1)
    
    for inv in pending:
        user = users_col.find_one({"user_id": inv['user_id']})
        name = user.get('name', 'ناشناس') if user else inv['user_id']
        kb.add(InlineKeyboardButton(f"👤 {name} - {inv['amount']:,} تومان", callback_data=f"view_inv_{inv['_id']}"))
    
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_receipts"))
    await callback.message.edit_text("⏳ لیست رسیدهای منتظر تایید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("view_inv_"), state="*")
async def view_single_invoice(callback: types.CallbackQuery):
    inv_id = callback.data.split("_")[2]
    inv = invoices_col.find_one({"_id": ObjectId(inv_id)})
    
    if inv:
        text = f"📑 جزئیات رسید:\n👤 کاربر: {inv['user_id']}\n💰 مبلغ فاکتور: {inv['amount']:,} تومان\n📅 تاریخ: {inv.get('date', 'نامعلوم')}"
        # اگر آدرس عکس رسید ذخیره شده باشد، ادمین باید بتواند ببیند
        if 'photo_id' in inv:
            await bot.send_photo(callback.from_user.id, inv['photo_id'], caption=text, reply_markup=nav.receipt_action_menu(inv_id))
        else:
            await callback.message.answer(text, reply_markup=nav.receipt_action_menu(inv_id))
    await callback.answer()

# --- ۲. شارژ همگانی ---
@dp.callback_query_handler(lambda c: c.data == "charge_all", state="*")
async def start_all_charge(callback: types.CallbackQuery):
    await AdminStates.waiting_for_all_charge_amount.set()
    await callback.message.answer("💰 مبلغ شارژ هدیه برای «همه» کاربران را وارد کنید (به تومان):", 
                                  reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 انصراف", callback_data="admin_charge_wallet")))

@dp.message_handler(state=AdminStates.waiting_for_all_charge_amount)
async def confirm_charge_all_step(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ لطفاً فقط عدد وارد کنید.")
    
    amount = int(message.text)
    await state.update_data(all_amount=amount)
    await message.answer(f"❓ آیا از شارژ همگانی مبلغ {amount:,} تومان برای تمام کاربران مطمئن هستید؟", 
                         reply_markup=nav.confirm_all_charge(amount))

@dp.callback_query_handler(lambda c: c.data.startswith("confirm_all_"), state=AdminStates.waiting_for_all_charge_amount)
async def process_all_charge(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data.get('all_amount')
    
    users = users_col.find({})
    count = 0
    for u in users:
        users_col.update_one({"user_id": u['user_id']}, {"$inc": {"balance": amount}})
        try:
            await bot.send_message(u['user_id'], f"🎁 تبریک! کیف پول شما مبلغ {amount:,} تومان شارژ شد.")
        except: continue
        count += 1
    
    await state.finish()
    await callback.message.edit_text(f"✅ عملیات موفق! {count} کاربر شارژ شدند.")

# --- ۳. آمار کاربران ---
@dp.callback_query_handler(lambda c: c.data == "admin_stats", state="*")
async def show_stats(callback: types.CallbackQuery):
    total_users = users_col.count_documents({})
    total_payments = invoices_col.count_documents({"status": "success"})
    
    text = f"📊 آمار ربات آراد VIP:\n\n" \
           f"👥 کل کاربران: {total_users} نفر\n" \
           f"✅ کل تراکنش‌های موفق: {total_payments}\n" \
           f"🚀 ربات در وضعیت آنلاین قرار دارد."
    
    await callback.message.edit_text(text, reply_markup=nav.admin_panel())
