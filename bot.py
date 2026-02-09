import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ----------------- Logging -----------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------- تعرفه‌ها -----------------
V2RAY_SUBS = [
    {"name": "V2Ray 1 ماهه", "price": "150,000 IRR"},
    {"name": "V2Ray 3 ماهه", "price": "400,000 IRR"},
    {"name": "V2Ray 6 ماهه", "price": "750,000 IRR"},
]

BIUVIU_SUBS = [
    {"name": "BiuvIU تک کاربره", "price": "100,000 IRR"},
    {"name": "BiuvIU چند کاربره", "price": "180,000 IRR"},
]

# ----------------- منوها -----------------
def main_menu():
    keyboard = [
        [InlineKeyboardButton("اشتراک‌های V2Ray", callback_data="v2ray")],
        [InlineKeyboardButton("اشتراک‌های BiuvIU", callback_data="biuviu")],
        [InlineKeyboardButton("پشتیبانی", callback_data="support")],
    ]
    return InlineKeyboardMarkup(keyboard)

def v2ray_menu():
    keyboard = [[InlineKeyboardButton(f"{sub['name']} - {sub['price']}", callback_data=f"v2ray_{i}")] for i, sub in enumerate(V2RAY_SUBS)]
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

def biuviu_menu():
    keyboard = [[InlineKeyboardButton(f"{sub['name']} - {sub['price']}", callback_data=f"biuviu_{i}")] for i, sub in enumerate(BIUVIU_SUBS)]
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)

def support_menu():
    keyboard = [
        [InlineKeyboardButton("تماس با پشتیبانی", url="https://t.me/YourSupport")],
        [InlineKeyboardButton("بازگشت", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ----------------- Handlers -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! لطفاً یک گزینه انتخاب کنید:", reply_markup=main_menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data

    if data == "v2ray":
        await query.edit_message_text("اشتراک‌های V2Ray:", reply_markup=v2ray_menu())
    elif data.startswith("v2ray_"):
        index = int(data.split("_")[1])
        sub = V2RAY_SUBS[index]
        await query.edit_message_text(f"شما اشتراک '{sub['name']}' با قیمت {sub['price']} را انتخاب کردید.\nبرای خرید با پشتیبانی تماس بگیرید.", reply_markup=support_menu())
    elif data == "biuviu":
        await query.edit_message_text("نوع BiuvIU VPN:", reply_markup=biuviu_menu())
    elif data.startswith("biuviu_"):
        index = int(data.split("_")[1])
        sub = BIUVIU_SUBS[index]
        await query.edit_message_text(f"شما اشتراک '{sub['name']}' با قیمت {sub['price']} را انتخاب کردید.\nبرای خرید با پشتیبانی تماس بگیرید.", reply_markup=support_menu())
    elif data == "support":
        await query.edit_message_text("پشتیبانی:", reply_markup=support_menu())
    elif data == "back":
        await query.edit_message_text("منوی اصلی:", reply_markup=main_menu())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("از دکمه‌ها برای ناوبری استفاده کنید.")

# ----------------- Main -----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN_HERE").build()
    app.add_handler(CommandHandler("start", start))