ADMIN_ID = 863961919
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def admin_verify_payment(invoice_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ تایید و شارژ", callback_data=f"verify_pay_{invoice_id}"),
        InlineKeyboardButton("❌ رد تراکنش", callback_data=f"reject_pay_{invoice_id}")
    )
    return kb

# --- منوی اصلی ---
def main_menu(user_id):
    kb = InlineKeyboardMarkup(row_width=2)
    
    # دکمه‌های عمومی برای همه
    kb.add(InlineKeyboardButton("🛍 خرید اشتراک جدید", callback_data="buy_new"))
    kb.add(InlineKeyboardButton("🎁 دریافت اشتراک تست", callback_data="get_test"))
    
    kb.row(
        InlineKeyboardButton("📜 اشتراک‌های من", callback_data="my_subs"), 
        InlineKeyboardButton("🧾 فاکتورهای من", callback_data="my_invs")
    )
    
    kb.add(InlineKeyboardButton("👤 حساب کاربری", callback_data="my_account"))
    
    kb.row(
        InlineKeyboardButton("📞 پشتیبانی", callback_data="support"), 
        InlineKeyboardButton("📚 آموزش اتصال", url="https://t.me/AradVIPTeaching")
    )
    
    kb.add(InlineKeyboardButton("📊 وضعیت سرویس‌ها", url="http://v2inj.galexystore.ir:3001/"))

    # --- بخش مدیریت (فقط برای ادمین) ---
    # حتماً هر دو طرف مقایسه رو به string تبدیل کن که خیالمون راحت باشه
    if str(user_id) == str(ADMIN_ID):
        kb.add(InlineKeyboardButton("⚙️ پنل مدیریت", callback_data="admin_panel"))
        
    return kb

# --- منوی خرید سرویس ---
def buy_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🚀 V2ray (Vision + Reality)", callback_data="buy_v2ray"),
        InlineKeyboardButton("🛡 Biubiu VPN (تک کاربره)", callback_data="buy_biubiu_1u"),
        InlineKeyboardButton("👥 Biubiu VPN (دو کاربره)", callback_data="buy_biubiu_2u"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
    )
    return kb


# --- روش‌های پرداخت فاکتور ---
def payment_methods(inv_id):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("💰 پرداخت از موجودی کیف پول", callback_data=f"pay_wallet_{inv_id}"),
        InlineKeyboardButton("💎 شارژ حساب و پرداخت (ارز دیجیتال)", callback_data="charge_crypto"),
        InlineKeyboardButton("❌ لغو و بازگشت", callback_data="main_menu")
    )
    return kb

# --- منوی بخش شارژ ارز دیجیتال ---
def charge_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🔹 TETHER (USDT) + 20% هدیه", callback_data="charge_usdt"),
        InlineKeyboardButton("🔸 TRON (TRX) + 20% هدیه", callback_data="charge_trx"),
        InlineKeyboardButton("💎 TON Coin + 20% هدیه", callback_data="charge_ton"),
        InlineKeyboardButton("🔙 بازگشت به حساب", callback_data="my_account")
    )
    return kb

# --- انتخاب شبکه تتر ---
def usdt_networks():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("TRC20 (پیشنهادی)", callback_data="net_usdt_trc20"),
        InlineKeyboardButton("ERC20", callback_data="net_usdt_erc20"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="charge_crypto")
    )
    return kb

# --- مدیریت اشتراک‌ها (دکمه تمدید) ---
def sub_details_menu(inv_id):
    kb = InlineKeyboardMarkup(row_width=1)
    # اضافه کردن یک زیرخط اضافه قبل از inv_id برای هماهنگی با split("_")[2]
    kb.add(
        InlineKeyboardButton("♻️ تمدید این اشتراک", callback_data=f"renew_request_{inv_id}"),
        InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="my_subs")
    )
    return kb


# --- منوی بخش تست ---
def test_subs_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("V2ray (رایگان)", callback_data="test_v2ray"),
        InlineKeyboardButton("Biubiu VPN (تست ۱ روزه)", callback_data="test_biubiu"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
    )
    return kb

def v2ray_test_confirm():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("✅ دریافت اشتراک تست", callback_data="confirm_v2ray_test"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="get_test")
    )
    return kb

def biubiu_test_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("⏱ ۱ روزه نامحدود - ۵۰,۰۰۰ تومان", callback_data="plan_biu_50000_1DayTest"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="get_test")
    )
    return kb

# --- منوی اصلی پنل مدیریت ---
def admin_panel():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📑 رسیدها", callback_data="admin_receipts"),
        InlineKeyboardButton("💰 شارژ کیف پول", callback_data="admin_charge_wallet")
    )
    kb.add(
        InlineKeyboardButton("✉️ پیام به کاربران", callback_data="admin_broadcast"),
        InlineKeyboardButton("📊 آمار کاربران", callback_data="admin_stats")
    )
    kb.add(InlineKeyboardButton("⚙️ تنظیمات کاربران", callback_data="admin_user_settings"))
    kb.add(InlineKeyboardButton("🔙 خروج از پنل", callback_data="main_menu"))
    return kb

# --- منوی رسیدها ---
def admin_receipts_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("⏳ رسیدهای تایید نشده", callback_data="receipts_pending"),
        InlineKeyboardButton("✅ رسیدهای تایید شده", callback_data="receipts_confirmed"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
    )
    return kb

# --- عملیات روی یک رسید مشخص ---
def receipt_action_menu(inv_id):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("✅ تایید (شارژ خودکار)", callback_data=f"verify_pay_{inv_id}"),
        InlineKeyboardButton("❌ رد رسید", callback_data=f"reject_pay_{inv_id}"),
        InlineKeyboardButton("➕ شارژ دستی مبلغ دلخواه", callback_data=f"manual_charge_{inv_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="receipts_pending")
    )
    return kb

# --- منوی شارژ کیف پول ---
def admin_charge_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("👤 شارژ تکی", callback_data="charge_single"),
        InlineKeyboardButton("👥 شارژ همگانی", callback_data="charge_all")
    )
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel"))
    return kb

# --- تایید نهایی شارژ همگانی ---
def confirm_all_charge(amount):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ بله، مطمئنم", callback_data=f"confirm_all_{amount}"),
        InlineKeyboardButton("❌ خیر، لغو شود", callback_data="admin_charge_wallet")
    )
    return kb
# منوی عملیات روی کاربر (برای شارژ تکی یا تنظیمات)
def admin_user_ops_menu(target_user_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💰 شارژ حساب", callback_data=f"op_charge_{target_user_id}"),
        InlineKeyboardButton("✉️ ارسال پیام", callback_data=f"op_msg_{target_user_id}")
    )
    kb.add(
        InlineKeyboardButton("❌ حذف کاربر", callback_data=f"op_delete_{target_user_id}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
    )
    return kb


def register_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📲 اشتراک‌گذاری شماره موبایل", request_contact=True))
    return kb

