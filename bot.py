import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- تنظیمات ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "12345678"))
CARD_NUMBER = "5057851560122225"
CARD_NAME = "سجاد رستگاران"

# --- تعرفه‌ها ---
V2RAY_SUBS = [
    {"name": "5 گیگ زمان نامحدود", "price": 60000},
    {"name": "10 گیگ زمان نامحدود", "price": 100000},
    {"name": "20 گیگ زمان نامحدود", "price": 150000},
    {"name": "30 گیگ زمان نامحدود", "price": 200000},
    {"name": "50 گیگ زمان نامحدود", "price": 300000},
    {"name": "100 گیگ زمان نامحدود", "price": 400000},
    {"name": "200 گیگ زمان نامحدود", "price": 500000},
]

BIUVIU_SINGLE = [
    {"name": "1 ماهه", "price": 100000},
    {"name": "2 ماهه", "price": 200000},
    {"name": "3 ماهه", "price": 300000},
]

BIUVIU_MULTI = [
    {"name": "1 ماهه نامحدود", "price": 300000},
    {"name": "3 ماهه نامحدود", "price": 500000},
    {"name": "6 ماهه نامحدود", "price": 1100000},
    {"name": "12 ماهه نامحدود", "price": 1200000},
]

user_wallets = {}

def get_wallet(user_id):
    return user_wallets.get(user_id, 0)

# ---- هندلرهای منو ----

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💳 خرید اشتراک جدید", callback_data="buy_new")],
        [InlineKeyboardButton("👤 حساب کاربری و شارژ", callback_data="account")],
        [InlineKeyboardButton("📞 پشتیبانی", url="https://t.me/AradVIP")]
    ]
    text = "به ربات خوش آمدید. یکی از گزینه‌های زیر را انتخاب کنید:"
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def buy_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📡 v2ray", callback_data="v2ray_list")],
        [InlineKeyboardButton("🚀 biubiu VPN", callback_data="biubiu_menu")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="start")]
    ]
    await update.callback_query.message.edit_text("نوع سرویس خود را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

async def v2ray_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for sub in V2RAY_SUBS:
        keyboard.append([InlineKeyboardButton(f"{sub['name']} - {sub['price']:,} تومان", callback_data=f"buy_service_v2_{sub['price']}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")])
    await update.callback_query.message.edit_text("تعرفه‌های v2ray:", reply_markup=InlineKeyboardMarkup(keyboard))

async def biubiu_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👤 1 کاربره", callback_data="biubiu_s")],
        [InlineKeyboardButton("👥 2 کاربره", callback_data="biubiu_m")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="buy_new")]
    ]
    await update.callback_query.message.edit_text("تعداد کاربر biubiu VPN را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

async def biubiu_s_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for sub in BIUVIU_SINGLE:
        keyboard.append([InlineKeyboardButton(f"{sub['name']} - {sub['price']:,} تومان", callback_data=f"buy_service_biu_{sub['price']}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="biubiu_menu")])
    await update.callback_query.message.edit_text("تعرفه‌های 1 کاربره biubiu:", reply_markup=InlineKeyboardMarkup(keyboard))

async def biubiu_m_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for sub in BIUVIU_MULTI:
        keyboard.append([InlineKeyboardButton(f"{sub['name']} - {sub['price']:,} تومان", callback_data=f"buy_service_biu_{sub['price']}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="biubiu_menu")])
    await update.callback_query.message.edit_text("تعرفه‌های 2 کاربره biubiu:", reply_markup=InlineKeyboardMarkup(keyboard))

# ---- سیستم خرید و کیف پول (مشابه قبل) ----

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    balance = get_wallet(user_id)
    text = f"👤 شناسه: `{user_id}`\n💰 موجودی: {balance:,} تومان"
    keyboard = [
        [InlineKeyboardButton("➕ شارژ کیف پول", callback_data="add_funds")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
    ]
    await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def add_funds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"💳 شماره کارت: `{CARD_NUMBER}`\n👤 بنام: {CARD_NAME}\n\nلطفاً پس از واریز، عکس رسید را بفرستید."
    context.user_data["waiting_for_receipt"] = True
    await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 انصراف", callback_data="account")]]), parse_mode="Markdown")

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_for_receipt") and (update.message.photo):
        user = update.message.from_user
        caption = f"📩 رسید جدید از: {user.id}\nمبلغ تایید شود؟"
        keyboard = [[InlineKeyboardButton("✅ ۵۰ ت", callback_data=f"conf_{user.id}_50000"), InlineKeyboardButton("✅ ۱۰۰ ت", callback_data=f"conf_{user.id}_100000")],
                    [InlineKeyboardButton("❌ رد", callback_data=f"rej_{user.id}")]]
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
        await update.message.reply_text("رسید ارسال شد.")
        context.user_data["waiting_for_receipt"] = False

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data.startswith("conf_"):
        _, uid, amt = query.data.split("_")
        user_wallets[int(uid)] = get_wallet(int(uid)) + int(amt)
        await context.bot.send_message(chat_id=int(uid), text=f"✅ حساب شما {amt} شارژ شد.")
        await query.edit_message_caption("🟢 تایید شد.")
    elif query.data.startswith("rej_"):
        uid = query.data.split("_")[1]
        await context.bot.send_message(chat_id=int(uid), text="❌ رسید شما رد شد.")
        await query.edit_message_caption("🔴 رد شد.")

# --- اجرا ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^start$"))
    app.add_handler(CallbackQueryHandler(buy_new, pattern="^buy_new$"))
    app.add_handler(CallbackQueryHandler(v2ray_list, pattern="^v2ray_list$"))
    app.add_handler(CallbackQueryHandler(biubiu_menu, pattern="^biubiu_menu$"))
    app.add_handler(CallbackQueryHandler(biubiu_s_list, pattern="^biubiu_s$"))
    app.add_handler(CallbackQueryHandler(biubiu_m_list, pattern="^biubiu_m$"))
    app.add_handler(CallbackQueryHandler(account, pattern="^account$"))
    app.add_handler(CallbackQueryHandler(add_funds, pattern="^add_funds$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(conf|rej)_"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    app.run_polling()
