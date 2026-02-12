from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types
def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🛍 خرید اشتراک جدید", callback_data="buy_new"))
    kb.add(InlineKeyboardButton("🎁 دریافت اشتراک تست", callback_data="get_test"))
    kb.row(InlineKeyboardButton("📜 اشتراک‌های من", callback_data="my_subs"), 
           InlineKeyboardButton("🧾 فاکتورهای من", callback_data="my_invs"))
    kb.add(InlineKeyboardButton("👤 حساب کاربری", callback_data="my_account"))
    kb.row(InlineKeyboardButton("📞 پشتیبانی", callback_data="support"), 
           InlineKeyboardButton("📚 آموزش اتصال", url="https://t.me/AradVIPTeaching"))
    kb.add(InlineKeyboardButton("📊 وضعیت سرویس‌ها", url="http://v2inj.galexystore.ir:3001/"))
    return kb

def buy_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("V2ray(تانل نیم بها+کاربرنامحدود)", callback_data="buy_v2ray"),
           InlineKeyboardButton("Biubiu VPN", callback_data="buy_biubiu"), # به هندلر انتخاب تعداد کاربر میره
           InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu"))
    return kb

def payment_methods(inv_id): # حتما inv_id بگیرد
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("💳 کارت به کارت", callback_data=f"pay_card_{inv_id}"),
        InlineKeyboardButton("💰 کیف پول", callback_data=f"pay_wallet_{inv_id}"),
        InlineKeyboardButton("❌ لغو و بازگشت", callback_data="main_menu")
    )
    return kb
def account_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("💳 شارژ کیف پول", callback_data="charge_wallet"),
        types.InlineKeyboardButton("🚀 سرویس‌های من", callback_data="my_services")
    )
    kb.add(types.InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu"))
    return kb
