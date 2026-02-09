# bot.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

BOT_TOKEN = "8531397872:AAHQbLN-Frn1GfTboMYpol36LkepNak1r3M"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------- منوی اصلی ----------
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("خرید گیفت کارت", callback_data="gift")],
        [InlineKeyboardButton("V2Ray", callback_data="v2ray")],
        [InlineKeyboardButton("BiuvIU", callback_data="biuviu")],
        [InlineKeyboardButton("پشتیبانی", callback_data="support")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ---------- منوی V2Ray ----------
def v2ray_menu():
    # نمونه دکمه‌ها بدون نیاز به فایل subscriptions.py
    keyboard = [
        [InlineKeyboardButton("اشتراک 1 ماهه", callback_data="v2_1")],
        [InlineKeyboardButton("اشتراک 3 ماهه", callback_data="v2_3")],
        [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data="main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ---------- منوی BiuvIU ----------
def biuviu_menu():
    keyboard = [
        [InlineKeyboardButton("سرویس تک کاربره", callback_data="biu_single")],
        [InlineKeyboardButton("سرویس چند کاربره", callback_data="biu_multi")],
        [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data="main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ---------- هندلر start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! به ربات خوش اومدی 🎮",
        reply_markup=main_menu_keyboard()
    )

# ---------- هندلر کلیک روی دکمه ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "gift":
        await query.edit_message_text("شما گزینه خرید گیفت کارت را انتخاب کردید.")
    elif query.data == "v2ray":
        await query.edit_message_text("اشتراک‌های V2Ray:", reply_markup=v2ray_menu())
    elif query.data == "biuviu":
        await query.edit_message_text("نوع BiuvIU VPN:", reply_markup=biuviu_menu())
    elif query.data in ["v2_1", "v2_3", "biu_single", "biu_multi"]:
        await query.edit_message_text(f"شما گزینه {query.data} را انتخاب کردید.")
    elif query.data == "main":
        await query.edit_message_text("بازگشت به منوی اصلی:", reply_markup=main_menu_keyboard())
    elif query.data == "support":
        await query.edit_message_text("برای پشتیبانی با ما تماس بگیرید.")

# ---------- main ----------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("ربات در حال اجراست...")
    app.run_polling()