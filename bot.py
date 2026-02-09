import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- تنظیمات ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "12345678")) # آیدی عددی خودت را در Railway ست کن
CARD_NUMBER = os.getenv("CARD_NUMBER", "6037-xxxx-xxxx-xxxx")
CARD_NAME = os.getenv("CARD_NAME", "نام شما")

# --- دیتابیس مجازی (در دنیای واقعی باید از SQLite استفاده کنی) ---
# نکته: با ریستارت شدن Railway این مقادیر صفر می‌شوند. برای دائمی شدن نیاز به دیتابیس است.
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
    user_id = update.callback_query.from_user.id
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
    await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

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
        # ارسال برای ادمین
        caption = f"📩 رسید جدید دریافت شد!\n\n👤 کاربر: {user.first_name}\n🆔 آیدی: `{user.id}`\n\nآیا واریز تایید می‌شود؟"
        keyboard = [
            [InlineKeyboardButton("✅ تایید و شارژ ۵۰ تومانی", callback_data=f"confirm_{user.id}_50000")],
            [InlineKeyboardButton("✅ تایید و شارژ ۱۰۰ تومانی", callback_data=f"confirm_{user.id}_100000")],
            [InlineKeyboardButton("❌ رد رسید", callback_data=f"reject_{user.id}")]
        ]
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
        context.user_data["waiting_for_receipt"] = False
        await update.message.reply_text("✅ رسید شما برای مدیریت ارسال شد. پس از بررسی، موجودی شما افزایش می‌یابد.")

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data.startswith("confirm_"):
        _, user_id, amount = data.split("_")
        user_id = int(user_id)
        amount = int(amount)
        
        # شارژ کیف پول
        user_wallets[user_id] = get_wallet(user_id) + amount
        
        await query.answer(f"حساب کاربر {user_id} شارژ شد.")
        await query.edit_message_caption(caption=query.message.caption + "\n\n🟢 **تایید و شارژ شد.**")
        await context.bot.send_message(chat_id=user_id, text=f"🎉 واریز شما تایید شد!\n💰 مبلغ {amount:,} تومان به کیف پول شما اضافه شد.")

    elif data.startswith("reject_"):
        user_id = int(data.split("_")[1])
        await query.answer("رسید رد شد.")
        await query.edit_message_caption(caption=query.message.caption + "\n\n🔴 **رد شد.**")
        await context.bot.send_message(chat_id=user_id, text="❌ متأسفانه رسید واریز شما توسط مدیریت رد شد. در صورت بروز مشکل با پشتیبانی در ارتباط باشید.")

# ---- اجرا ----
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(confirm|reject)_"))
app.add_handler(CallbackQueryHandler(button)) # همان دکمه‌های قبلی شما
app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_receipt))
app.run_polling()
