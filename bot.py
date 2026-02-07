import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# ====== تنظیمات ======
TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [123456789]  # ادمین‌ها
ADMIN_TELEGRAM = "@AradVIP"  # آی‌دی تلگرام ادمین

# ====== دیتای موقت ======
users_wallet = {}  # user_id: balance
users_subscriptions = {}  # user_id: [subscriptions]

# ====== اشتراک‌ها ======
v2ray_subscriptions = {
    "5GB": 69000,
    "10GB": 109000,
    "30GB": 149000,
    "50GB": 189000,
    "100GB": 329000,
    "200GB": 429000,
    "300GB": 560000
}

biubiu_single = {
    "یک ماهه (1 توکن)": 100000,
    "دو ماهه (2 توکن)": 200000,
    "سه ماهه (3 توکن)": 300000
}

biubiu_double = {
    "یک ماهه": 170000,
    "سه ماهه": 300000,
    "شش ماهه": 500000,
    "یک ساله": 1200000
}

# ====== منوها ======
def main_menu():
    buttons = [
        [InlineKeyboardButton("💳 خرید اشتراک جدید", callback_data="buy_new")],
        [InlineKeyboardButton("📊 اشتراک های من", callback_data="my_subscriptions")],
        [InlineKeyboardButton("💰 کیف پول", callback_data="wallet")],
        [InlineKeyboardButton("📌 اشتراک تست", callback_data="test_subscription")],
        [InlineKeyboardButton("📞 پشتیبانی", callback_data="support")],
        [InlineKeyboardButton("📘 آموزش اتصال", callback_data="tutorial")]
    ]
    return InlineKeyboardMarkup(buttons)

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]])

# ====== خرید اشتراک جدید ======
def vpn_selection_menu():
    buttons = [
        [InlineKeyboardButton("V2Ray", callback_data="vpn_v2ray")],
        [InlineKeyboardButton("Biubiu VPN", callback_data="vpn_biubiu")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)

# ====== Biubiu VPN ======
def biubiu_type_menu():
    buttons = [
        [InlineKeyboardButton("تک کاربره", callback_data="biubiu_single")],
        [InlineKeyboardButton("دو کاربره", callback_data="biubiu_double")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def biubiu_single_menu():
    buttons = [[InlineKeyboardButton(f"{name} → {price:,}", callback_data=f"biubiu_single_{name}")] for name, price in biubiu_single.items()]
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_biubiu_type")])
    return InlineKeyboardMarkup(buttons)

def biubiu_double_menu():
    buttons = [[InlineKeyboardButton(f"{name} → {price:,}", callback_data=f"biubiu_double_{name}")] for name, price in biubiu_double.items()]
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_biubiu_type")])
    return InlineKeyboardMarkup(buttons)

# ====== اشتراک تست ======
def test_subscription_menu():
    buttons = [
        [InlineKeyboardButton("تست V2Ray", callback_data="test_v2ray")],
        [InlineKeyboardButton("تست Biubiu VPN", callback_data="test_biubiu")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)

# ====== اشتراک V2Ray ======
def v2ray_subscription_menu():
    buttons = [[InlineKeyboardButton(f"{name} → {price:,}", callback_data=f"sub_{name}")] for name, price in v2ray_subscriptions.items()]
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)

# ====== کیف پول ======
def wallet_menu(user_id):
    balance = users_wallet.get(user_id, 0)
    buttons = [
        [InlineKeyboardButton("💳 شارژ کارت به کارت", callback_data="wallet_topup_card")],
        [InlineKeyboardButton("💰 استفاده از موجودی کیف پول", callback_data="wallet_use")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(buttons)

# ====== دستورات ربات ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
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

    # ====== خرید اشتراک جدید ======
    if data == "buy_new":
        await query.edit_message_text("📌 نوع VPN را انتخاب کنید:", reply_markup=vpn_selection_menu())

    elif data == "vpn_v2ray":
        await query.edit_message_text("📌 اشتراک V2Ray را انتخاب کنید:", reply_markup=v2ray_subscription_menu())

    elif data == "vpn_biubiu":
        await query.edit_message_text("📌 Biubiu VPN را انتخاب کنید:", reply_markup=biubiu_type_menu())

    # ====== Biubiu نوع تک کاربره و دو کاربره ======
    elif data == "biubiu_single":
        await query.edit_message_text("📌 اشتراک تک کاربره Biubiu VPN را انتخاب کنید:", reply_markup=biubiu_single_menu())

    elif data == "biubiu_double":
        await query.edit_message_text("📌 اشتراک دو کاربره Biubiu VPN را انتخاب کنید:", reply_markup=biubiu_double_menu())

    elif data.startswith("biubiu_single_"):
        name = data.replace("biubiu_single_", "")
        price = biubiu_single[name]
        await query.edit_message_text(
            f"💰 قیمت: {price:,} تومان\n"
            f"📌 می‌توانید پرداخت را از طریق کارت به کارت یا کیف پول انجام دهید.",
            reply_markup=wallet_menu(user_id)
        )

    elif data.startswith("biubiu_double_"):
        name = data.replace("biubiu_double_", "")
        price = biubiu_double[name]
        await query.edit_message_text(
            f"💰 قیمت: {price:,} تومان\n"
            f"📌 می‌توانید پرداخت را از طریق کارت به کارت یا کیف پول انجام دهید.",
            reply_markup=wallet_menu(user_id)
        )

    # ====== V2Ray اشتراک ======
    elif data.startswith("sub_"):
        name = data.replace("sub_", "")
        price = v2ray_subscriptions[name]
        await query.edit_message_text(
            f"💰 قیمت: {price:,} تومان\n"
            f"📌 می‌توانید پرداخت را از طریق کارت به کارت یا کیف پول انجام دهید.",
            reply_markup=wallet_menu(user_id)
        )

    # ====== کیف پول ======
    elif data == "wallet":
        balance = users_wallet.get(user_id, 0)
        await query.edit_message_text(f"💰 موجودی شما: {balance:,} تومان", reply_markup=wallet_menu(user_id))

    elif data == "wallet_topup_card":
        await query.edit_message_text(
            "📌 برای شارژ کیف پول، مبلغ را کارت به کارت واریز کنید و بعد اطلاع دهید.\n"
            "🔹 شماره کارت: 6037991234567890",
            reply_markup=back_button()
        )

    elif data == "wallet_use":
        await query.edit_message_text("📌 از موجودی کیف پول برای خرید اشتراک استفاده کنید (بعد از انتخاب اشتراک)", reply_markup=back_button())

    # ====== اشتراک تست ======
    elif data == "test_subscription":
        await query.edit_message_text("📌 انتخاب اشتراک تست:", reply_markup=test_subscription_menu())
    elif data == "test_v2ray":
        await query.edit_message_text("✅ اشتراک تست V2Ray برای شما فعال شد!", reply_markup=back_button())
    elif data == "test_biubiu":
        await query.edit_message_text("✅ اشتراک تست Biubiu VPN برای شما فعال شد!", reply_markup=back_button())

    # ====== منوی اصلی ======
    elif data == "my_subscriptions":
        subs = users_subscriptions.get(user_id, [])
        if subs:
            text = "📊 اشتراک های شما:\n" + "\n".join(subs)
        else:
            text = "📊 شما هنوز اشتراکی خریداری نکردید"
        await query.edit_message_text(text, reply_markup=back_button())

    elif data == "support":
        await query.edit_message_text(
            f"📞 برای ارتباط با ادمین، لطفاً به آی‌دی زیر پیام دهید:\n{ADMIN_TELEGRAM}",
            reply_markup=back_button()
        )

    elif data == "tutorial":
        await query.edit_message_text(
            "📘 آموزش اتصال و راهنمایی‌ها در کانال آموزش‌ها موجود است:\n"
            "https://t.me/AradVIPTeaching",
            reply_markup=back_button()
        )

    elif data == "back_main":
        await query.edit_message_text("🔙 برگشت به منوی اصلی:", reply_markup=main_menu())

# ====== اجرای ربات ======
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()