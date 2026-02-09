# bot.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# ---------- تنظیمات ----------
BOT_TOKEN = "8531397872:AAHQbLN-Frn1GfTboMYpol36LkepNak1r3M"

# ---------- لاگینگ ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------- متن خوش آمد ----------
WELCOME_TEXT = "سلام! به ربات گیمینگ خوش اومدی 🎮\nلطفا یکی از گزینه‌ها رو انتخاب کن:"

# ---------- منوی اصلی ----------
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("خرید گیفت کارت", callback_data="gift")],
        [InlineKeyboardButton("شارژ حساب", callback_data="wallet")],
        [InlineKeyboardButton("پشتیبانی", callback_data="support")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ---------- هندلر دستور start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=main_menu_keyboard()
    )

# ---------- هندلر کلیک روی دکمه ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "gift":
        await query.edit_message_text("شما گزینه خرید گیفت کارت را انتخاب کردید.")
    elif query.data == "wallet":
        await query.edit_message_text("شما گزینه شارژ حساب را انتخاب کردید.")
    elif query.data == "support":
        await query.edit_message_text("شما گزینه پشتیبانی را انتخاب کردید.")

# ---------- main ----------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("ربات در حال اجراست...")
    app.run_polling()