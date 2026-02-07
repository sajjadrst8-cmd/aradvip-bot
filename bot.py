import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("توکن BOT_TOKEN در Environment Variables تعریف نشده است!")

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 حساب کاربری", callback_data="account")],
        [InlineKeyboardButton("💬 پشتیبانی", callback_data="support")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ربات تستی شما آماده است!", reply_markup=main_menu())

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "account":
        await q.edit_message_text("👤 اینجا حساب کاربری شما نمایش داده می‌شود.", reply_markup=main_menu())
    elif q.data == "support":
        await q.edit_message_text("💬 جهت ارتباط با ادمین:\n@AradVIP", reply_markup=main_menu())

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.run_polling()

if __name__ == "__main__":
    main()