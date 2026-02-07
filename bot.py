# bot.py
import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import csv

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- دیتابیس ساده ---
USERS = {}  # اطلاعات کاربر
SUBSCRIPTIONS = {}  # اشتراک‌ها
ADMINS = [123456789]  # ایدی ادمین ها

# --- نرخ اشتراک‌ها ---
V2RAY_SUBS = {
    "5 گیگ": 69000, "10 گیگ": 109000, "30 گیگ": 149000,
    "50 گیگ": 189000, "100 گیگ": 329000, "200 گیگ": 429000,
    "300 گیگ": 560000
}

BIUBIU_SINGLE = {
    "یک ماهه": 167000, "دو ماهه": 334000, "سه ماهه": 500000
}

BIUBIU_DOUBLE = {
    "یک ماهه": 297000, "سه ماهه": 780000, "شش ماهه": 1270000, "یک ساله": 1690000
}

# --- Keyboards ---
def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 خرید اشتراک جدید", callback_data="buy_subscription")],
        [InlineKeyboardButton("🎁 دریافت اشتراک تست", callback_data="test_subscription")],
        [InlineKeyboardButton("👤 حساب کاربری", callback_data="account")],
        [InlineKeyboardButton("📞 پشتیبانی", callback_data="support"),
         InlineKeyboardButton("📚 آموزش اتصال", callback_data="tutorial")]
    ])

def account_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ افزایش موجودی", callback_data=f"add_balance_{user_id}")],
        [InlineKeyboardButton("👥 زیرمجموعه گیری", callback_data=f"referral_{user_id}")],
        [InlineKeyboardButton("📝 اشتراک‌های من", callback_data=f"my_subs_{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ])

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 گزارش مالی", callback_data="admin_financial")],
        [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")],
        [InlineKeyboardButton("💳 مدیریت اشتراک‌ها", callback_data="admin_subs")],
        [InlineKeyboardButton("➕ افزودن ادمین", callback_data="admin_add")],
        [InlineKeyboardButton("➖ حذف ادمین", callback_data="admin_remove")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
    ])

def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]])

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USERS.setdefault(user.id, {
        "username": user.username or "",
        "balance": 0,
        "subscriptions": [],
        "referrals": [],
        "join_date": datetime.now().strftime("%Y/%m/%d")
    })
    if user.id in ADMINS:
        await update.message.reply_text("به پنل ادمین خوش آمدید!", reply_markup=admin_keyboard())
    else:
        await update.message.reply_text("لطفا یکی از گزینه های زیر رو انتخاب کنید", reply_markup=main_keyboard())

# --- Callback Handlers ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # --- کاربران عادی ---
    if query.data == "buy_subscription":
        # دکمه‌های v2ray و biubiu
        keyboard = [
            [InlineKeyboardButton("v2ray", callback_data="buy_v2ray")],
            [InlineKeyboardButton("biubiu VPN", callback_data="buy_biubiu")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
        ]
        await query.edit_message_text("انتخاب سرویس:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == "test_subscription":
        keyboard = [
            [InlineKeyboardButton("تست v2ray", callback_data="test_v2ray")],
            [InlineKeyboardButton("تست biubiu VPN", callback_data="test_biubiu")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
        ]
        await query.edit_message_text("اشتراک تست:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == "account":
        user = USERS.get(user_id)
        text = f"👤 شناسه کاربری: {user_id}\n🔐 وضعیت: 👤 کاربر عادی\n💰 موجودی کیف پول: {user['balance']} تومان\n👥 تعداد زیرمجموعه‌ها: {len(user['referrals'])}\n📆 تاریخ عضویت: {user['join_date']}"
        await query.edit_message_text(text, reply_markup=account_keyboard(user_id))
    
    elif query.data.startswith("add_balance_"):
        await query.edit_message_text("لطفا مبلغ مورد نظر برای شارژ کیف پول را وارد کنید:", reply_markup=back_keyboard())
    
    elif query.data.startswith("referral_"):
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.edit_message_text(f"لینک اختصاصی شما:\n{link}", reply_markup=back_keyboard())
    
    elif query.data.startswith("my_subs_"):
        user = USERS.get(user_id)
        if user['subscriptions']:
            text = "📦 اشتراک‌های شما:\n" + "\n".join(user['subscriptions'])
        else:
            text = "شما هنوز اشتراکی ندارید."
        await query.edit_message_text(text, reply_markup=back_keyboard())
    
    elif query.data == "support":
        await query.edit_message_text("برای ارتباط با ادمین:\n@AradVIP", reply_markup=back_keyboard())
    
    elif query.data == "tutorial":
        await query.edit_message_text("📚 آموزش اتصال: [لینک کانال آموزش](https://t.me/YourTutorialChannel)", parse_mode="Markdown", reply_markup=back_keyboard())
    
    # --- بازگشت به منوی اصلی ---
    elif query.data == "back_main":
        if user_id in ADMINS:
            await query.edit_message_text("پنل ادمین:", reply_markup=admin_keyboard())
        else:
            await query.edit_message_text("منوی اصلی:", reply_markup=main_keyboard())
    
    # --- پنل ادمین ---
    elif user_id in ADMINS:
        if query.data.startswith("admin"):
            await query.edit_message_text(f"پنل ادمین: {query.data}", reply_markup=back_keyboard())

# --- دریافت متن ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if text.isdigit():
        USERS[user_id]["balance"] += int(text)
        await update.message.reply_text(f"💰 کیف پول شما شارژ شد! موجودی: {USERS[user_id]['balance']} تومان", reply_markup=main_keyboard())
    else:
        await update.message.reply_text("پیام دریافت شد.", reply_markup=main_keyboard())

# --- Main ---
def main():
    TOKEN = os.getenv("BOT_TOKEN")  # توکن از Environment Variable میاد
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
