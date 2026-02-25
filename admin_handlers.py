from aiogram import types
from aiogram.dispatcher import FSMContext
from loader import dp, bot, ADMIN_ID
import markups as nav
import qrcode
import io
import re
import marzban_handlers
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

# استیت‌های جدید برای بخش مدیریت کاربر
class UserManageStates(StatesGroup):
    waiting_for_user_search = State() # جستجوی کاربر
    waiting_for_single_amount = State() # مبلغ شارژ تکی
    waiting_for_direct_msg = State() # متن پیام مستقیم

# --- شروع جستجوی کاربر (برای شارژ یا پیام) ---
@dp.callback_query_handler(lambda c: c.data in ["charge_single", "admin_user_settings", "admin_broadcast"], state="*")
async def start_user_search(callback: types.CallbackQuery):
    await UserManageStates.waiting_for_user_search.set()
    await callback.message.answer("🔍 آیدی عددی (User ID) کاربر مورد نظر را ارسال کنید:\n(می‌توانید از بخش آمار یا رسیدها آیدی را کپی کنید)")
    await callback.answer()

@dp.message_handler(state=UserManageStates.waiting_for_user_search)
async def process_user_search(message: types.Message, state: FSMContext):
    search_id = message.text
    if not search_id.isdigit():
        return await message.answer("⚠️ آیدی باید عدد باشد. دوباره تلاش کنید:")
    
    user = users_col.find_one({"user_id": int(search_id)})
    if not user:
        return await message.answer("❌ کاربری با این آیدی در دیتابیس یافت نشد.")
    
    await state.update_data(target_id=search_id)
    text = f"👤 کاربر یافت شد:\n🆔 آیدی: {user['user_id']}\n💰 موجودی فعلی: {user.get('balance', 0):,} تومان\n📞 شماره: {user.get('phone', 'ثبت نشده')}"
    await message.answer(text, reply_markup=nav.admin_user_ops_menu(search_id))

# --- بخش شارژ تکی مبلغ دلخواه ---
@dp.callback_query_handler(lambda c: c.data.startswith("op_charge_"), state="*")
async def ask_charge_amount(callback: types.CallbackQuery, state: FSMContext):
    target_id = callback.data.split("_")[2]
    await state.update_data(target_id=target_id)
    await UserManageStates.waiting_for_single_amount.set()
    await callback.message.answer(f"💰 مبلغ شارژ برای کاربر {target_id} را به «تومان» وارد کنید:")

@dp.message_handler(state=UserManageStates.waiting_for_single_amount)
async def finish_single_charge(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("⚠️ مبلغ معتبر نیست.")
    
    data = await state.get_data()
    target_id = int(data.get('target_id'))
    amount = int(message.text)
    
    # آپدیت دیتابیس
    users_col.update_one({"user_id": target_id}, {"$inc": {"balance": amount}})
    
    # اطلاع به کاربر
    try:
        await bot.send_message(target_id, f"✅ حساب شما توسط مدیریت شارژ شد!\n💰 مبلغ: {amount:,} تومان")
    except: pass
    
    await message.answer(f"✅ مبلغ {amount:,} تومان به حساب {target_id} اضافه شد.", reply_markup=nav.admin_panel())
    await state.finish()

# --- بخش ارسال پیام مستقیم (چت) ---
@dp.callback_query_handler(lambda c: c.data.startswith("op_msg_"), state="*")
async def ask_direct_msg(callback: types.CallbackQuery, state: FSMContext):
    target_id = callback.data.split("_")[2]
    await state.update_data(target_id=target_id)
    await UserManageStates.waiting_for_direct_msg.set()
    await callback.message.answer(f"✉️ متن پیام خود را برای کاربر {target_id} بفرستید:")

@dp.message_handler(state=UserManageStates.waiting_for_direct_msg)
async def send_direct_msg(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_id = int(data.get('target_id'))
    
    try:
        await bot.send_message(target_id, f"✉️ پیام جدید از طرف مدیریت:\n\n{message.text}")
        await message.answer("✅ پیام با موفقیت ارسال شد.")
    except:
        await message.answer("❌ ارسال پیام ناموفق بود (احتمالاً کاربر ربات را بلاک کرده).")
    
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == "admin_charge_wallet", state="*")
async def back_to_admin_charge(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text("💰 بخش شارژ کیف پول:", reply_markup=nav.admin_charge_menu())

@dp.callback_query_handler(lambda c: c.data == "admin_stats", state="*")
async def show_stats(callback: types.CallbackQuery):
    token = await marzban_handlers.get_marzban_token()
    status = "✅ متصل به مرزبان" if token else "❌ خطا در اتصال به مرزبان"
    
    total_users = users_col.count_documents({})
    await callback.message.edit_text(
        f"📊 آمار ربات:\n\n👥 کل کاربران: {total_users}\n🔗 وضعیت پنل: {status}",
        reply_markup=nav.admin_panel()
    )
@dp.callback_query_handler(lambda c: c.data.startswith("admin:"), state="*")
async def admin_decision(call: types.CallbackQuery):
    # ساختار دیتا: admin:action:user_id:price:purpose
    data = call.data.split(":")
    action = data[1]
    target_user_id = data[2]
    amount = data[3]
    plan_name = data[4]

    # در فایل admin_handlers.py بخش accept را پیدا و اینگونه اصلاح کن:

    if action == "accept":
        try:
            # ۱. استخراج حجم و ساخت اکانت
            match = re.search(r'\d+', plan_name)
            data_gb = match.group() if match else "5"
            username = marzban_handlers.generate_random_username() #
            
            sub_url = await marzban_handlers.create_marzban_user(username, data_gb) #
            
            if sub_url:
                # ۲. ساخت QR Code در حافظه (بدون ذخیره فایل)
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(sub_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                byte_io = io.BytesIO()
                img.save(byte_io, 'PNG')
                byte_io.seek(0)

                # ۳. طراحی متن پیام مشابه عکس ارسالی شما
                caption_text = (
                    f"✅ **اشتراک شما با موفقیت فعال شد!**\n\n"
                    f"👤 **نام کاربری:** `{username}`\n"
                    f"🌐 **وضعیت:** `Active`\n"
                    f"📊 **حجم کل:** `{data_gb} GB`\n"
                    f"⏳ **تاریخ انقضا:** `بدون محدودیت`\n\n" # طبق تنظیمات expire=0 در marzban_handlers
                    f"🔗 **لینک اتصال:**\n`{sub_url}`\n\n"
                    f"📸 **راهنما:** QR Code بالا را در اپلیکیشن خود اسکن کنید یا لینک را کپی و Import کنید."
                )

                # ۴. ارسال عکس QR Code به همراه توضیحات برای کاربر
                await bot.send_photo(
                    chat_id=target_user_id,
                    photo=byte_io,
                    caption=caption_text,
                    parse_mode="Markdown"
                )
                
                # ۵. بروزرسانی پیام ادمین
                await call.message.edit_caption(f"✅ رسید تایید شد و اشتراک {data_gb}GB برای کاربر ارسال گردید.")
            else:
                await call.answer("❌ خطا در ساخت اکانت در پنل مرزبان", show_alert=True)

        except Exception as e:
            await call.answer(f"❌ خطای سیستم در تولید QR: {e}", show_alert=True)
            
    elif action == "reject":
        await bot.send_message(target_user_id, "❌ متاسفانه رسید ارسالی شما مورد تایید قرار نگرفت.\nدر صورت بروز مشکل با پشتیبانی در ارتباط باشید.")
        await call.message.edit_caption(f"❌ این رسید رد شد.\nکاربر: {target_user_id}")
    
    await call.answer()
