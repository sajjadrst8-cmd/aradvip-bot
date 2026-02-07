import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# ======= توکن از ENV Variable =======
TOKEN = os.getenv("BOT_TOKEN")

# ======= منوی اصلی =======
def main_menu():
    buttons = [
        [InlineKeyboardButton("💳 خرید اشتراک", callback_data="buy_subscription")],
        [InlineKeyboardButton("📊 اشتراک های من", callback_data="my_subscriptions")],
        [InlineKeyboardButton("📞 پشتیبانی", callback_data="support")],
        [InlineKeyboardButton("📘 آموزش اتصال", callback_data="tutorial")]
    ]
    return InlineKeyboardMarkup(buttons)

# ======= دستورات ربات =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! خوش آمدید به ربات AradVIP ✅\nگزینه مورد نظر خود را انتخاب کنید:",
        reply_markup=main_menu()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # برای جلوگیری از لودینگ دائمی در تلگرام

    if query.data == "buy_subscription":
        await query.edit_message_text("📌 اینجا می‌تونی اشتراک بخری (بعداً کامل اضافه می‌کنیم)")
    elif query.data == "my_subscriptions":
        await query.edit_message_text("📌 اشتراک های تو اینجا نمایش داده میشن (بعداً کامل اضافه می‌کنیم)")
    elif query.data == "support":
        await query.edit_message_text("📞 برای پشتیبانی با ما تماس بگیر!")
    elif query.data == "tutorial":
        await query.edit_message_text("📘 آموزش اتصال ربات و اشتراک ها اینجا نمایش داده میشه")
    else:
        await query.edit_message_text("❌ گزینه نامعتبر!")

# ======= اجرای ربات =======
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Command /start
    app.add_handler(CommandHandler("start", start))
    # Callback دکمه‌ها
    app.add_handler(CallbackQueryHandler(button_handler))

    # ربات 24 ساعته آنلاین
    app.run_polling()

# ======= شروع برنامه =======
if __name__ == "__main__":
    main()