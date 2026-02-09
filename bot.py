# bot.py
from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes
from keyboards import *
from messages import *
from marzban_api import MarzbanAPI
from config import TELEGRAM_BOT_TOKEN

# اتصال Marzban
marzban = MarzbanAPI.py()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, reply_markup=main_menu_keyboard())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # منوی خرید اشتراک جدید
    if data == "buy_new":
        keyboard = [
            [InlineKeyboardButton("V2Ray", callback_data="v2ray_menu")],
            [InlineKeyboardButton("Biuviu VPN", callback_data="biuviu_menu")],
            [InlineKeyboardButton(BACK, callback_data="back_main")]
        ]
        await query.edit_message_text(SUBSCRIPTION_MENU, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "v2ray_menu":
        await query.edit_message_text("اشتراک‌های V2Ray:", reply_markup=v2ray_menu())
    elif data.startswith("v2ray_"):
        idx = int(data.split("_")[1])
        sub = marzban.get_subscriptions()[idx]  # فقط نمونه، باید متناسب با ID ها باشه
        await query.edit_message_text(f"خرید {sub['name']} موفق بود!")

    elif data == "biuviu_menu":
        await query.edit_message_text("نوع BiuvIU VPN:", reply_markup=biuviu_menu())
    elif data == "biuviu_single":
        await query.edit_message_text("اشتراک‌های 1 کاربره:", reply_markup=biuviu_single_menu())
    elif data == "biuviu_multi":
        await query.edit_message_text("اشتراک‌های 2 کاربره:", reply_markup=biuviu_multi_menu())

    # بازگشت‌ها
    elif data.startswith("back"):
        await query.edit_message_text(WELCOME_TEXT, reply_markup=main_menu_keyboard())

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()