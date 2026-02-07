from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

TOKEN = "BOT_TOKEN_HERE"

# ================== دیتابیس موقت ==================
users = {}
pending_topups = {}

# ================== منوها ==================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 خرید اشتراک جدید", callback_data="buy")],
        [InlineKeyboardButton("👤 حساب کاربری", callback_data="account")],
        [InlineKeyboardButton("🎁 اشتراک تست", callback_data="test")],
        [InlineKeyboardButton("💬 پشتیبانی", callback_data="support")]
    ])

def back_menu(target="back_main"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data=target)]
    ])

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in users:
        users[uid] = {
            "balance": 0,
            "join": datetime.now().strftime("%Y/%m/%d - %H:%M")
        }
    await update.message.reply_text(
        "👋 به ربات AradVIP خوش آمدید",
        reply_markup=main_menu()
    )

# ================== CALLBACK ==================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data

    # ---------- بازگشت ----------
    if data == "back_main":
        await q.edit_message_text("🏠 منوی اصلی", reply_markup=main_menu())

    # ---------- حساب کاربری ----------
    elif data == "account":
        u = users[uid]
        await q.edit_message_text(
            f"""👤 شناسه کاربری: {uid}
🔐 وضعیت: 👤 کاربر عادی
💰 موجودی کیف پول: {u['balance']:,} تومان

📆 تاریخ عضویت: {u['join']}""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ افزایش موجودی", callback_data="topup")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
            ])
        )

    # ---------- افزایش موجودی ----------
    elif data == "topup":
        await q.edit_message_text(
            "💳 مبلغ افزایش موجودی را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💵 100,000 تومان", callback_data="topup_100")],
                [InlineKeyboardButton("💵 200,000 تومان", callback_data="topup_200")],
                [InlineKeyboardButton("💵 500,000 تومان", callback_data="topup_500")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="account")]
            ])
        )

    elif data.startswith("topup_") and data.split("_")[1].isdigit():
        amount = int(data.split("_")[1]) * 1000
        pending_topups[uid] = amount
        await q.edit_message_text(
            f"""💳 پرداخت کارت به کارت
مبلغ: {amount:,} تومان

📌 پس از پرداخت، رسید را ارسال کنید.""",
            reply_markup=back_menu("account")
        )

    # ---------- خرید ----------
    elif data == "buy":
        await q.edit_message_text(
            "📦 نوع اشتراک را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 V2Ray", callback_data="buy_v2ray")],
                [InlineKeyboardButton("📱 Biubiu VPN", callback_data="buy_biubiu")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
            ])
        )

    # ---------- V2Ray ----------
    elif data == "buy_v2ray":
        await q.edit_message_text(
            "🚀 پلن‌های V2Ray:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("5 گیگ | 69 هزار", callback_data="buy_69000")],
                [InlineKeyboardButton("10 گیگ | 109 هزار", callback_data="buy_109000")],
                [InlineKeyboardButton("30 گیگ | 149 هزار", callback_data="buy_149000")],
                [InlineKeyboardButton("50 گیگ | 189 هزار", callback_data="buy_189000")],
                [InlineKeyboardButton("100 گیگ | 329 هزار", callback_data="buy_329000")],
                [InlineKeyboardButton("200 گیگ | 429 هزار", callback_data="buy_429000")],
                [InlineKeyboardButton("300 گیگ | 560 هزار", callback_data="buy_560000")],
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
                [InlineKeyboardButton("1 ماهه | 100 هزار", callback_data="buy_100000")],
                [InlineKeyboardButton("2 ماهه | 200 هزار", callback_data="buy_200000")],
                [InlineKeyboardButton("3 ماهه | 300 هزار", callback_data="buy_300000")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_biubiu")]
            ])
        )

    elif data == "biu_double":
        await q.edit_message_text(
            "👥 دوکاربره:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("1 ماهه | 170 هزار", callback_data="buy_170000")],
                [InlineKeyboardButton("3 ماهه | 300 هزار", callback_data="buy_300000")],
                [InlineKeyboardButton("6 ماهه | 500 هزار", callback_data="buy_500000")],
                [InlineKeyboardButton("1 ساله | 1,200 هزار", callback_data="buy_1200000")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_biubiu")]
            ])
        )

    # ---------- پرداخت با موجودی ----------
    elif data.startswith("buy_") and data.split("_")[1].isdigit():
        price = int(data.split("_")[1])
        if users[uid]["balance"] < price:
            await q.edit_message_text(
                "❌ موجودی کیف پول کافی نیست",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ افزایش موجودی", callback_data="topup")],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="buy")]
                ])
            )
        else:
            users[uid]["balance"] -= price
            await q.edit_message_text(
                f"✅ خرید با موفقیت انجام شد\n💰 مبلغ کسر شده: {price:,} تومان",
                reply_markup=back_menu("back_main")
            )

    # ---------- تست ----------
    elif data == "test":
        await q.edit_message_text(
            "🎁 اشتراک تست:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 تست V2Ray", callback_data="back_main")],
                [InlineKeyboardButton("📱 تست Biubiu", callback_data="back_main")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
            ])
        )

    # ---------- پشتیبانی ----------
    elif data == "support":
        await q.edit_message_text(
            "💬 جهت ارتباط با ادمین:\n@AradVIP",
            reply_markup=back_menu("back_main")
        )

# ================== رسید پرداخت ==================
async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in pending_topups:
        amount = pending_topups.pop(uid)
        users[uid]["balance"] += amount
        await update.message.reply_text(
            f"✅ موجودی شما به مبلغ {amount:,} تومان افزایش یافت",
            reply_markup=main_menu()
        )

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.PHOTO | filters.DOCUMENT, receive_receipt))
    app.run_polling()

if __name__ == "__main__":
    main()