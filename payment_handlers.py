from aiogram import types
from aiogram.dispatcher import FSMContext
from loader import dp, bot, ADMIN_ID
import markups as nav
from states import BuyState

# بخشی از فایل payment_handlers.py

@dp.message_handler(content_types=['photo'], state=BuyState.waiting_for_receipt)
async def handle_payment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    price = data.get("price")
    plan_name = data.get("plan_name")

    try:
        # ارسال عکس به ادمین
        await bot.send_photo(
            chat_id=ADMIN_ID,
            photo=message.photo[-1].file_id,
            caption=(
                f"👤 **رسید جدید دریافت شد**\n\n"
                f"🆔 آیدی کاربر: `{user_id}`\n"
                f"💰 مبلغ واریزی: {price} تومان\n"
                f"💎 پلن انتخابی: {plan_name}"
            ),
            parse_mode="Markdown",
            reply_markup=nav.admin_verify_payment(user_id, price, plan_name)
        )

        # تایید به کاربر
        await message.answer(
            "✅ رسید شما با موفقیت برای مدیریت ارسال شد.\n"
            "لطفاً تا تایید نهایی صبور باشید.",
            reply_markup=nav.main_menu(user_id)
        )
        await state.finish()

    except Exception as e:
        await message.answer(f"❌ خطایی در ارسال رسید رخ داد: {e}")
