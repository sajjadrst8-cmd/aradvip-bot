from aiogram import types
from loader import dp
from config import V2RAY_PLANS
from aiogram.dispatcher import FSMContext

@dp.callback_query_handler(lambda c: c.data == "buy_v2ray")
async def v2ray_list(callback: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for text, price, name in V2RAY_PLANS:
        kb.add(types.InlineKeyboardButton(text, callback_data=f"plan_v2ray_{price}_{name}"))
    kb.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new"))
    await callback.message.edit_text("💎 لیست پلن‌های V2ray:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("plan_v2ray_"), state="*")
async def ask_username(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    await state.update_data(s_type="v2ray", price=int(parts[2]), plan_name=parts[3])
    await BuyState.entering_username.set()
    # دکمه نام تصادفی
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🎲 نام تصادفی", callback_data="random_name"))
    await callback.message.edit_text("لطفاً یوزرنیم دلخواه خود را وارد کنید:", reply_markup=kb)
