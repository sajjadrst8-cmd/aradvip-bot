from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8531397872:AAHmyli0cKo2w_Pkg4X9x-JZzE-NXVGsaaE"

# ----------------- منوها -----------------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 خرید اشتراک جدید", callback_data="buy")],
        [InlineKeyboardButton("🎁 اشتراک تست", callback_data="test")],
        [InlineKeyboardButton("💬 پشتیبانی", callback_data="support")]
    ])

def back_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
    ])

# ----------------- START -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 به ربات AradVIP خوش آمدید",
        reply_markup=main_menu()
    )

# ----------------- CALLBACK -----------------
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    # بازگشت
    if data == "back":
        await q.edit_message_text("🏠 منوی اصلی", reply_markup=main_menu())

    # خرید
    elif data == "buy":
        await q.edit_message_text(
            "📦 نوع اشتراک را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 V2Ray", callback_data="buy_v2ray")],
                [InlineKeyboardButton("📱 Biubiu VPN", callback_data="buy_biubiu")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
            ])
        )

    # ---------- V2Ray ----------
    elif data == "buy_v2ray":
        await q.edit_message_text(
            "🚀 پلن‌های V2Ray:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("5 گیگ | 69 هزار", callback_data="pay")],
                [InlineKeyboardButton("10 گیگ | 109 هزار", callback_data="pay")],
                [InlineKeyboardButton("30 گیگ | 149 هزار", callback_data="pay")],
                [InlineKeyboardButton("50 گیگ | 189 هزار", callback_data="pay")],
                [InlineKeyboardButton("100 گیگ | 329 هزار", callback_data="pay")],
                [InlineKeyboardButton("200 گیگ | 429 هزار", callback_data="pay")],
                [InlineKeyboardButton("300 گیگ | 560 هزار", callback_data="pay")],
                [InlineKeyboardButton("➕ حجم اضافه", callback_data="pay")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="buy")]
            ])
        )

    # ---------- Biubiu ----------
    elif data == "buy_biubiu":
        await q.edit_message_text(
            "📱 Biubiu VPN:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 تک‌کاربره", callback_data="biu_single")],
                [InlineKeyboardButton("👥 دوکاربره", callback_data="biu_double")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="buy")]
            ])
        )

    elif data == "biu_single":
        await q.edit_message_text(
            "👤 تک‌کاربره:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("1 ماهه | 100 هزار", callback_data="pay")],
                [InlineKeyboardButton("2 ماهه | 200 هزار", callback_data="pay")],
                [InlineKeyboardButton("3 ماهه | 300 هزار", callback_data="pay")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_biubiu")]
            ])
        )

    elif data == "biu_double":
        await q.edit_message_text(
            "👥 دوکاربره:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("1 ماهه | 170 هزار", callback_data="pay")],
                [InlineKeyboardButton("3 ماهه | 300 هزار", callback_data="pay")],
                [InlineKeyboardButton("6 ماهه | 500 هزار", callback_data="pay")],
                [InlineKeyboardButton("1 ساله | 1,200 هزار", callback_data="pay")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_biubiu")]
            ])
        )

    # پرداخت (فعلاً نمایشی)
    elif data == "pay":
        await q.edit_message_text(
            "💳 روش پرداخت را انتخاب کنید:\n(در مرحله بعد فعال می‌شود)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 کیف پول", callback_data="back")],
                [InlineKeyboardButton("💳 کارت به کارت", callback_data="back")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
            ])
        )

    # تست
    elif data == "test":
        await q.edit_message_text(
            "🎁 دریافت اشتراک تست:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 تست V2Ray", callback_data="back")],
                [InlineKeyboardButton("📱 تست Biubiu", callback_data="back")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
            ])
        )

    # پشتیبانی
    elif data == "support":
        await q.edit_message_text(
            "💬 جهت ارتباط با ادمین:\n@AradVIP",
            reply_markup=back_btn()
        )

# ----------------- MAIN -----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.run_polling()

if __name__ == "__main__":
    main()