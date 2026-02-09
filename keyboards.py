# keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from messages import *

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton(BUY_NEW, callback_data="buy_new")],
        [InlineKeyboardButton(TEST_SUB, callback_data="test_sub")],
        [InlineKeyboardButton(ACCOUNT, callback_data="account")],
        [
            InlineKeyboardButton(SUPPORT, callback_data="support"),
            InlineKeyboardButton(GUIDE, callback_data="guide")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def v2ray_menu():
    from subscriptions import V2RAY_SUBS
    keyboard = [[InlineKeyboardButton(f"{sub['name']} - {sub['price']:,} تومان", callback_data=f"v2ray_{i}")]
                for i, sub in enumerate(V2RAY_SUBS)]
    keyboard.append([InlineKeyboardButton(BACK, callback_data="back_buy")])
    return InlineKeyboardMarkup(keyboard)

def biuviu_menu():
    from subscriptions import BIUVIU_SINGLE, BIUVIU_MULTI
    keyboard = [
        [InlineKeyboardButton("1 کاربره", callback_data="biuviu_single")],
        [InlineKeyboardButton("2 کاربره", callback_data="biuviu_multi")],
        [InlineKeyboardButton(BACK, callback_data="back_buy")]
    ]
    return InlineKeyboardMarkup(keyboard)

def biuviu_single_menu():
    from subscriptions import BIUVIU_SINGLE
    keyboard = [[InlineKeyboardButton(f"{sub['name']} - {sub['price']:,} تومان", callback_data=f"biu_single_{i}")]
                for i, sub in enumerate(BIUVIU_SINGLE)]
    keyboard.append([InlineKeyboardButton(BACK, callback_data="back_biu_single")])
    return InlineKeyboardMarkup(keyboard)

def biuviu_multi_menu():
    from subscriptions import BIUVIU_MULTI
    keyboard = [[InlineKeyboardButton(f"{sub['name']} - {sub['price']:,} تومان", callback_data=f"biu_multi_{i}")]
                for i, sub in enumerate(BIUVIU_MULTI)]
    keyboard.append([InlineKeyboardButton(BACK, callback_data="back_biu_multi")])
    return InlineKeyboardMarkup(keyboard)