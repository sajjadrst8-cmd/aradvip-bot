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

# --- ۱. هندلر دستور استارت (منتقل شده از main) ---
@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message):
    referrer = message.get_args()
    user = await get_user(message.from_user.id, referrer)
    
    if referrer and str(referrer).isdigit() and int(referrer) != message.from_user.id:
        try:
            await bot.send_message(referrer, f"🔔 کاربر {message.from_user.id} با لینک دعوت شما وارد ربات شد.")
        except:
            pass
    await message.answer("لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=nav.main_menu())

# --- ۲. تایید ادمین (منتقل شده از main) ---
@dp.callback_query_handler(lambda c: c.data.startswith("admin_"), state="*")
async def admin_verify(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    status, uid, amt = parts[1], int(parts[2]), float(parts[3])

    if status == "ok":
        await users_col.update_one({"user_id": uid}, {"$inc": {"wallet": amt}})
        try:
            await bot.send_message(uid, f"✅ رسید شما تأیید شد!\nمبلغ {amt:,} تومان به حساب شما اضافه شد.")
        except: pass
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ تأیید و شارژ شد.")
    else:
        try:
            await bot.send_message(uid, "❌ رسید شما رد شد. لطفاً با پشتیبانی در ارتباط باشید.")
        except: pass
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ رد شد.")
    await callback.answer()

# --- ۳. شروع فرآیند خرید ---
@dp.callback_query_handler(lambda c: c.data == "buy_new")
async def buy_start(callback: types.CallbackQuery):
    await callback.message.edit_text("لطفاً نوع اشتراک خودتون رو انتخاب کنید:", reply_markup=nav.buy_menu())

@dp.callback_query_handler(lambda c: c.data == "buy_v2ray")
async def v2ray_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    plans = [("5گیگ ۱۰۰ت", 100000), ("10گیگ ۱۵۰ت", 150000), ("20گیگ ۲۰۰ت", 200000)]
    for text, price in plans:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"plan_v2ray_{price}_{text[:5]}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new"))
    await callback.message.edit_text("لطفاً پلن V2ray را انتخاب کنید:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("plan_"))
async def ask_username(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    await state.update_data(price=int(parts[2]), plan_name=parts[3], type="V2ray")
    await BuyState.entering_username.set()
    await callback.message.edit_text("👤 نام کاربری (3-32 کاراکتر) را وارد کنید:")

@dp.message_handler(state=BuyState.entering_username)
async def validate_username(message: types.Message, state: FSMContext):
    username = message.text.lower()
    if len(username) < 3 or len(username) > 32:
        return await message.answer("⚠️ نامعتبر است. دوباره تلاش کنید:")
    
    data = await state.get_data()
    inv = await add_invoice(message.from_user.id, {'price': data['price'], 'plan': data['plan_name'], 'type': data['type'], 'username': username})
    
    text = f"✅ فاکتور ایجاد شد\n💰 مبلغ: {inv['amount']:,} تومان\n👤 کاربر: {username}"
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("💳 پرداخت", callback_data=f"pay_{inv['inv_id']}"),
        types.InlineKeyboardButton("🎟 کد تخفیف", callback_data="apply_off")
    )
    await message.answer(text, reply_markup=kb)

# --- ۴. بخش Biubiu و بقیه هندلرها ---
@dp.callback_query_handler(lambda c: c.data == "buy_biubiu")
async def biubiu_menu(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("👤 تک کاربره", callback_data="biu_1"),
           types.InlineKeyboardButton("👥 دو کاربره", callback_data="biu_2"))
    await callback.message.edit_text("نوع Biubiu را انتخاب کنید:", reply_markup=kb)

# --- ۵. شارژ کیف پول و کارت به کارت ---
@dp.callback_query_handler(lambda c: c.data == "charge_wallet")
async def start_charge(callback: types.CallbackQuery):
    await BuyState.charging_wallet.set()
    await callback.message.answer("💰 مبلغ شارژ (تومان) را وارد کنید:")

@dp.message_handler(state=BuyState.charging_wallet)
async def process_charge_amt(message: types.Message, state: FSMContext):
    amt = int(message.text)
    inv = await add_invoice(message.from_user.id, {'price': amt, 'plan': 'شارژ', 'type': '💰 شارژ'})
    await message.answer(f"✅ فاکتور شارژ {amt:,} تومان ایجاد شد.", 
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("پرداخت", callback_data=f"pay_{inv['inv_id']}")))
    await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith("pay_"), state="*")
async def payment_choice(callback: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("💳 کارت به کارت", callback_data="method_card"),
        types.InlineKeyboardButton("💰 کیف پول", callback_data="method_wallet")
    )
    await callback.message.edit_text("روش پرداخت:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "method_card", state="*")
async def card_info(callback: types.CallbackQuery):
    await BuyState.waiting_for_receipt.set()
    await callback.message.answer("📸 عکس رسید را بفرستید:\n💳 کارت: `5057851560122222` بنام سجاد رستگاران")

@dp.message_handler(content_types=['photo'], state=BuyState.waiting_for_receipt)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    price = data.get('price', 0)
    kb = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✅ تایید", callback_data=f"admin_ok_{message.from_user.id}_{price}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"admin_no_{message.from_user.id}_0")
    )
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"رسید از {message.from_user.id}\nمبلغ: {price}", reply_markup=kb)
    await message.answer("⏳ رسید ارسال شد. منتظر تایید بمانید.")
    await state.finish()

# --- ۶. مدیریت و تخفیف ---
@dp.message_handler(commands=['admin'], user_id=ADMIN_ID)
async def admin_panel(message: types.Message):
    await message.answer("🛠 پنل مدیریت\nبرای شارژ: `/setwallet ID AMOUNT`", parse_mode="Markdown")

@dp.message_handler(commands=['setwallet'], user_id=ADMIN_ID)
async def set_wallet(message: types.Message):
    args = message.get_args().split()
    await users_col.update_one({"user_id": int(args[0])}, {"$set": {"wallet": float(args[1])}})
    await message.answer("✅ انجام شد.")
