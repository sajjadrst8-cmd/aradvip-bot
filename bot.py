import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- تنظیمات (مقادیر را داخل " " بگذارید) ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "12345678")) # آیدی عددی خودت
CARD_NUMBER = "6037-9999-8888-7777"  # شماره کارت خودت
CARD_NAME = "سجاد رستگاران"           # نام صاحب کارت

# دیتابیس موقت در حافظه
user_wallets = {}

def get_wallet(user_id):
    return user_wallets.get(user_id, 0)

# ---- منوها ----
def main_menu():
    keyboard = [
        [InlineKeyboardButton("💳 خرید اشتراک", callback_data="buy_new")],
        [InlineKeyboardButton("👤 حساب کاربری و شارژ", callback_data="account")],
        [InlineKeyboardButton("📞 پشتیبانی", url="https://t.me/AradVIP")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "به ربات خوش آمدید. لطفاً انتخاب کنید:"
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu())
    else:
        await update.callback_query.message.edit_text(text, reply_markup=main_menu())

async def account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    balance = get_wallet(user_id)
    text = (
        f"👤 شناسه: `{user_id}`\n"
        f"💰 موجودی کیف پول: {balance:,} تومان\n\n"
        "برای خرید اشتراک، باید ابتدا کیف پول خود را شارژ کنید."
    )
    keyboard = [
        [InlineKeyboardButton("➕ شارژ کیف پول (کارت به کارت)", callback_data="add_funds")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def add_funds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔴 **مراحل شارژ کیف پول:**\n\n"
        f"1️⃣ مبلغ مورد نظر را به کارت زیر واریز کنید:\n\n"
        f"💳 `{CARD_NUMBER}`\n"
        f"👤 بنام: **{CARD_NAME}**\n\n"
        "2️⃣ **سپس تصویر رسید واریز را همین‌جا ارسال کنید.**\n"
        "پس از تأیید مدیریت، حساب شما شارژ می‌شود."
    )
    context.user_data["waiting_for_receipt"] = True
    await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 انصراف", callback_data="account")]]), parse_mode="Markdown")

# ---- دریافت رسید توسط ادمین ----
async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_for_receipt") and (update.message.photo or update.message.document):
        user = update.message.from_user
        caption = f"📩 رسید جدید!\n👤 کاربر: {user.first_name}\n🆔 آیدی: `{user.id}`\n\nتایید و شارژ چقدر انجام شود؟"
        keyboard = [
            [InlineKeyboardButton("✅ ۵۰ هزار تومان", callback_data=f"conf_{user.id}_50000")],
            [InlineKeyboardButton("✅ ۱۰۰ هزار تومان", callback_data=f"conf_{user.id}_100000")],
            [InlineKeyboardButton("❌ رد رسید", callback_data=f"rej_{user.id}")]
        ]
        # ارسال عکس برای ادمین
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
        context.user_data["waiting_for_receipt"] = False
        await update.message.reply_text("✅ رسید برای مدیریت ارسال شد. منتظر تایید بمانید.")

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data.startswith("conf_"):
        _, user_id, amount = data.split("_")
        user_id, amount = int(user_id), int(amount)
        user_wallets[user_id] = get_wallet(user_id) + amount
        await query.edit_message_caption(caption=query.message.caption + f"\n\n🟢 تایید شد (+{amount:,})")
        await context.bot.send_message(chat_id=user_id, text=f"🎉 حساب شما مبلغ {amount:,} تومان شارژ شد.")

    elif data.startswith("rej_"):
        user_id = int(data.split("_")[1])
        await query.edit_message_caption(caption=query.message.caption + "\n\n🔴 رسید رد شد.")
        await context.bot.send_message(chat_id=user_id, text="❌ رسید واریز شما توسط مدیریت رد شد.")

# --- اجرای ربات ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^start$"))
    app.add_handler(CallbackQueryHandler(account, pattern="^account$"))
    app.add_handler(CallbackQueryHandler(add_funds, pattern="^add_funds$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(conf|rej)_"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_receipt))
    
    print("Bot is running...")
    app.run_polling()
