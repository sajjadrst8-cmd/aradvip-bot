ADMIN_ID = 12345678
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


# --- منوی اصلی ---
def main_menu(user_id=None):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(row_width=2)
    
    kb.add(InlineKeyboardButton("🛍 خرید اشتراک جدید", callback_data="buy_new"))
    kb.add(InlineKeyboardButton("🎁 دریافت اشتراک تست", callback_data="get_test"))
    
    # بقیه دکمه‌ها را اینجا اضافه کن...
    
    # بخش حساس که ارور می‌دهد را با try بپوشان
    try:
        if str(user_id) == str(ADMIN_ID):
            kb.add(InlineKeyboardButton("⚙️ پنل مدیریت", callback_data="admin_panel"))
    except:
        pass # اگر ADMIN_ID نبود، حداقل ربات کرش نکند
        
    return kb



# --- منوی خرید سرویس ---
def buy_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🚀 V2ray (Vision + Reality)", callback_data="buy_v2ray"),
           InlineKeyboardButton("🛡 Biubiu VPN", callback_data="buy_biubiu"),
           InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu"))
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

# --- پنل مدیریت ---
def admin_panel():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📊 آمار کلی ربات", callback_data="admin_stats"),
        InlineKeyboardButton("💰 شارژ دستی کاربر", callback_data="admin_manual_charge"),
        InlineKeyboardButton("🔙 خروج از پنل", callback_data="main_menu")
    )
    return kb

def admin_reject_reasons_menu(user_id):
    kb = InlineKeyboardMarkup(row_width=1)
    reasons = [
        ("❌ مبلغ واریزی اشتباه است", "mablagh"),
        ("❌ رسید جعلی یا تکراری است", "fake"),
        ("❌ تصویر ارسالی واضح نیست", "blurry"),
        ("❌ مبلغی به حساب واریز نشده", "not_received")
    ]
    for text, reason_key in reasons:
        kb.add(InlineKeyboardButton(text, callback_data=f"admin_final_no_{user_id}_{reason_key}"))

    kb.add(InlineKeyboardButton("🔙 انصراف", callback_data="admin_main_panel"))
    return kb

def main_menu(user_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text="🛍 خرید اشتراک", callback_data="buy_plan"),
        InlineKeyboardButton(text="👤 اشتراک‌های من", callback_data="my_subs")
    )
    # اگر کاربر جزو لیست ادمین‌ها بود، دکمه پنل را اضافه کن
    if user_id == ADMIN_ID: # یا لیستی از ادمین‌ها
        kb.add(InlineKeyboardButton(text="⚙️ پنل مدیریت", callback_data="admin_panel"))
    
    return kb

def register_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📲 اشتراک‌گذاری شماره موبایل", request_contact=True))
    return kb

