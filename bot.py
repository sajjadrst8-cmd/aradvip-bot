import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# ====== تنظیمات ======
TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [123456789]  # ادمین‌ها، می‌تونی اضافه کنی

# ====== دیتای موقت ======
users_wallet = {}  # user_id: balance
users_subscriptions = {}  # user_id: [subscriptions]

# ====== منوها ======
def main_menu():
    buttons = [
        [InlineKeyboardButton("💳 خرید اشتراک", callback_data="buy_subscription")],
        [InlineKeyboardButton("📊 اشتراک های من", callback_data="my_subscriptions")],
        [InlineKeyboardButton("💰 کیف پول", callback_data="wallet")],
        [InlineKeyboardButton("📞 پشتیبانی", callback_data="support")],
        [InlineKeyboardButton("📘 آموزش اتصال", callback_data="tutorial")]
    ]
    return InlineKeyboardMarkup(buttons)

def admin_menu():
    buttons = [
        [InlineKeyboardButton("📥 بررسی پرداخت‌ها", callback_data="admin_payments")],
        [InlineKeyboardButton("👥 مدیریت ادمین‌ها", callback_data="admin_manage")],
        [InlineKeyboardButton("📊 گزارش مالی", callback_data="admin_report")]
    ]
    return InlineKeyboardMarkup(buttons)

# ====== خرید اشتراک ======
subscriptions_list = {
    "5GB": 69000,
    "10GB": 109000,
    "30GB": 149000,
    "50GB": 189000,
    "100GB": 329000,
    "200GB": 429000,
    "300GB": 560000
}

def subscription_buttons():
    buttons = []
    for name, price in subscriptions_list.items():
        buttons.append([InlineKeyboardButton(f"{name} → {price:,} تومان", callback_data=f"sub_{name}")])
    return InlineKeyboardMarkup(buttons)

# ====== دستورات ربات ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ADMINS:
        await update.message.reply_text("👑 پنل ادمین", reply_markup=admin_menu())
    else:
        if user_id not in users_wallet:
            users_wallet[user_id] = 0
            users_subscriptions[user_id] = []
        await update.message.reply_text(
            "سلام! خوش آمدید به ربات AradVIP ✅\nگزینه مورد نظر خود را انتخاب کنید:",
            reply_markup=main_menu()
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # ===== کاربران =====
    if data == "buy_subscription":
        await query.edit_message_text("📌 اشتراک مورد نظر خود را انتخاب کنید:", reply_markup=subscription_buttons())
    elif data.startswith("sub_"):
        sub_name = data.split("_")[1]
        price = subscriptions_list[sub_name]
        balance = users_wallet.get(user_id, 0)
        if balance >= price:
            users_wallet[user_id] -= price
            users_subscriptions[user_id].append(sub_name)
            await query.edit_message_text(f"✅ اشتراک {sub_name} خریداری شد!\n💰 موجودی باقی‌مانده: {users_wallet[user_id]:,} تومان")
        else:
            await query.edit_message_text(f"❌ موجودی کافی نیست! موجودی شما: {balance:,} تومان")
    elif data == "my_subscriptions":
        subs = users_subscriptions.get(user_id, [])
        if subs:
            text = "📊 اشتراک های شما:\n" + "\n".join(subs)
        else:
            text = "📊 شما هنوز اشتراکی خریداری نکردید"
        await query.edit_message_text(text)
    elif data == "wallet":
        balance = users_wallet.get(user_id, 0)
        await query.edit_message_text(f"💰 موجودی شما: {balance:,} تومان\nبرای افزایش موجودی با ادمین تماس بگیرید")
    elif data == "support":
        await query.edit_message_text("📞 برای پشتیبانی با ما تماس بگیر!")
    elif data == "tutorial":
        await query.edit_message_text("📘 آموزش اتصال ربات و اشتراک ها اینجا نمایش داده میشه")

    # ===== ادمین =====
    elif data == "admin_payments":
        await query.edit_message_text("📥 لیست پرداخت‌ها و تایید آنها (بعداً کامل می‌کنیم)")
    elif data == "admin_manage":
        await query.edit_message_text("👥 مدیریت ادمین‌ها: اضافه / حذف (بعداً کامل می‌کنیم)")
    elif data == "admin_report":
        await query.edit_message_text("📊 گزارش مالی و فروش (بعداً کامل می‌کنیم)")
    else:
        await query.edit_message_text("❌ گزینه نامعتبر!")

# ====== اجرای ربات ======
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()