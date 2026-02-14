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
           InlineKeyboardButton("Biubiu VPN", callback_data="buy_biubiu"),
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
    kb = InlineKeyboardMarkup(row_width=2)
    # اصلاح شده: تمام کدهای اجرایی حذف و فقط دکمه‌ها باقی ماندند
    kb.add(
        InlineKeyboardButton("💳 شارژ کیف پول", callback_data="charge_wallet"),
        InlineKeyboardButton("🚀 سرویس‌های من", callback_data="my_services")
    )
    kb.add(InlineKeyboardButton("💰 زیرمجموعه‌گیری (کسب درآمد)", callback_data="referral_section"))
    kb.add(InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu"))
    return kb

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
           InlineKeyboardButton("Biubiu VPN", callback_data="buy_biubiu"),
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

def wallet_charge_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("50,000", callback_data="charge_50000"),
        InlineKeyboardButton("100,000", callback_data="charge_100000"),
        InlineKeyboardButton("200,000", callback_data="charge_200000"),
        InlineKeyboardButton("500,000", callback_data="charge_500000")
    )
    # اضافه کردن دکمه مبلغ دلخواه
    kb.add(InlineKeyboardButton("➕ مبلغ دلخواه (تایپ مبلغ)", callback_data="charge_custom"))
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="my_account"))
    return kb
