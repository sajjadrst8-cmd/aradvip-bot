from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8531397872:AAHQbLN-Frn1GfTboMYpol36LkepNak1r3M"
# --- تعرفه‌ها ---
subscriptions = {
    "v2ray": {"name": "V2Ray", "price": "50,000 تومان", "details": "اشتراک V2Ray - 30 روزه"},
    "biubiu": {"name": "Biubiu VPN", "price": "40,000 تومان", "details": "اشتراک Biubiu VPN - 30 روزه"},
}

# --- منوی اصلی ---
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("خرید اشتراک جدید", callback_data="buy_subscription")],
        [InlineKeyboardButton("دریافت اشتراک تست", callback_data="test_subscription")],
        [InlineKeyboardButton("حساب کاربری", callback_data="account")],
        [
            InlineKeyboardButton("پشتیبانی", callback_data="support"),
            InlineKeyboardButton("آموزش اتصال", callback_data="tutorial")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- دکمه‌های خرید اشتراک ---
def subscription_keyboard():
    keyboard = [
        [InlineKeyboardButton(f"{subscriptions['v2ray']['name']} - {subscriptions['v2ray']['price']}", callback_data="v2ray")],
        [InlineKeyboardButton(f"{subscriptions['biubiu']['name']} - {subscriptions['biubiu']['price']}", callback_data="biubiu")],
        [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("به ربات خوش آمدید 🎉", reply_markup=main_menu_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # جلوگیری از ارور

    data = query.data

    if data == "buy_subscription":
        await query.edit_message_text("📦 سرویس مورد نظر خود را انتخاب کنید:", reply_markup=subscription_keyboard())

    elif data in subscriptions:
        sub = subscriptions[data]
        await query.edit_message_text(f"✅ شما سرویس {sub['name']} را انتخاب کردید.\n💰 قیمت: {sub['price']}\n📄 جزئیات: {sub['details']}")

    elif data == "test_subscription":
        await query.edit_message_text("🧪 اشتراک تست شما آماده است!")

    elif data == "account":
        user_id = query.from_user.id
        await query.edit_message_text(f"👤 آیدی شما: {user_id}\nزیرمجموعه: 0\nاشتراک فعال: ندارد")

    elif data == "support":
        await query.edit_message_text("💬 برای پشتیبانی با @SupportContact در ارتباط باشید")

    elif data == "tutorial":
        await query.edit_message_text("📚 آموزش اتصال: ... (لینک یا متن آموزش اینجا)")

    elif data == "main_menu":
        await query.edit_message_text("به منوی اصلی برگشتید:", reply_markup=main_menu_keyboard())

    else:
        await query.edit_message_text("❌ گزینه نامعتبر")

# --- Main ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()