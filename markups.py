from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🛍 خرید اشتراک جدید", callback_data="buy_new"))
    kb.add(InlineKeyboardButton("🎁 دریافت اشتراک تست", callback_data="get_test"))
    kb.row(InlineKeyboardButton("📜 اشتراک‌های من", callback_data="my_subs"), 
           InlineKeyboardButton("🧾 فاکتورهای من", callback_data="my_invs"))
    kb.add(InlineKeyboardButton("👤 حساب کاربری", callback_data="account"))
    kb.row(InlineKeyboardButton("📞 پشتیبانی", callback_data="support"), 
           InlineKeyboardButton("📚 آموزش اتصال", url="https://t.me/AradVIPTeaching"))
    kb.add(InlineKeyboardButton("📊 وضعیت سرویس‌ها", url="http://v2inj.galexystore.ir:3001/"))
    return kb

def buy_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("V2ray(تانل نیم بها+کاربرنامحدود)", callback_data="buy_v2ray"),
           InlineKeyboardButton("Biubiu VPN", callback_data="buy_biubiu"),
           InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu"))
    return kb

def payment_methods(price):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card"),
           InlineKeyboardButton("💰 کیف پول", callback_data="pay_wallet"),
           InlineKeyboardButton("🎟 اعمال کد تخفیف", callback_data="apply_off"),
           InlineKeyboardButton("❌ لغو فاکتور", callback_data="main_menu"))
    return kb
