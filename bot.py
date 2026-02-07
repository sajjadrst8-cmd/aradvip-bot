# bot.py
import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# دیتابیس ساده با دیکشنری (برای نسخه اولیه)
USERS = {}
SUBSCRIPTIONS = {}
ADMINS = [123456789]  # ایدی خودت اضافه کن

# Helper functions
def get_user_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 خرید اشتراک جدید", callback_data="buy_subscription")],
        [InlineKeyboardButton("🎁 دریافت اشتراک تست", callback_data="test_subscription")],
        [InlineKeyboardButton("👤 حساب کاربری", callback_data="account")],
        [InlineKeyboardButton("📞 پشتیبانی", callback_data="support"), InlineKeyboardButton("📚 آموزش اتصال", callback_data="tutorial")]
    ])

def get_account_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ افزایش موجودی", callback_data=f"add_balance_{user_id}")],
        [InlineKeyboardButton("👥 زیرمجموعه گیری", callback_data=f"referral_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]])

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USERS.setdefault(user.id, {
        "username": user.username or "",
        "balance": 0,
        "subscriptions": [],
        "referrals": [],
        "join_date": datetime.now().strftime("%Y/%m/%d")
    })
    await update.message.reply_text("به ربات خوش آمدید!", reply_markup=get_user_keyboard())

# Callback Handlers
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    if query.data == "buy_subscription":
        await query.edit_message_text("💳 انتخاب نوع اشتراک:\n(مثال: v2ray یا biubiu vpn)", reply_markup=get_back_keyboard())
    elif query.data == "test_subscription":
        await query.edit_message_text("🎁 انتخاب اشتراک تست:\nv2ray یا biubiu vpn", reply_markup=get_back_keyboard())
    elif query.data == "account":
        user = USERS.get(user_id)
        text = f"👤 شناسه کاربری: {user_id}\n🔐 وضعیت: 👤 کاربر عادی\n💰 موجودی کیف پول: {user['balance']} تومان\n👥 تعداد زیرمجموعه‌ها: {len(user['referrals'])}\n📆 تاریخ عضویت: {user['join_date']}"
        await query.edit_message_text(text, reply_markup=get_account_keyboard(user_id))
    elif query.data.startswith("add_balance_"):
        await query.edit_message_text("لطفا مبلغ مورد نظر برای شارژ کیف پول را وارد کنید:", reply_markup=get_back_keyboard())
    elif query.data.startswith("referral_"):
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.edit_message_text(f"لینک اختصاصی شما برای زیرمجموعه‌ها:\n{link}", reply_markup=get_back_keyboard())
    elif query.data == "support":
        await query.edit_message_text("برای ارتباط با ادمین به آیدی زیر پیام دهید:\n@AradVIP", reply_markup=get_back_keyboard())
    elif query.data == "tutorial":
        await query.edit_message_text("📚 آموزش اتصال: [لینک کانال آموزش](https://t.me/YourTutorialChannel)", parse_mode="Markdown", reply_markup=get_back_keyboard())
    elif query.data == "back_main":
        await query.edit_message_text("منوی اصلی:", reply_markup=get_user_keyboard())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    # شارژ کیف پول
    if text.isdigit():
        amount = int(text)
        USERS[user_id]["balance"] += amount
        await update.message.reply_text(f"💰 کیف پول شما با موفقیت شارژ شد! موجودی فعلی: {USERS[user_id]['balance']} تومان", reply_markup=get_user_keyboard())
    else:
        await update.message.reply_text("پیام دریافت شد.", reply_markup=get_user_keyboard())

# Main
def main():
    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
