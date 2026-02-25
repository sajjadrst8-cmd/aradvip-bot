import aiohttp
import string
import random
import config
import time
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from loader import dp, bot
from database import add_subscription # این تابع را در database.py که قبلا حرفش را زدیم اضافه کن

# استیت‌های خرید
class BuyState(StatesGroup):
    entering_username = State()
    waiting_for_receipt = State()
    entering_custom_amount = State()

# --- توابع پایه اتصال به API ---

async def get_marzban_token():
    payload = {
        'username': config.MARZBAN_USER, 
        'password': config.MARZBAN_PASS
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{config.PANEL_URL}/api/admin/token", data=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['access_token']
                return None
        except Exception as e:
            print(f"Marzban Token Error: {e}")
            return None

async def create_marzban_user(user_id, username, data_gb):
    """ساخت کاربر دقیقاً طبق تنظیمات تصویر پنل و ذخیره در دیتابیس"""
    token = await get_marzban_token()
    if not token: return None
    
    headers = {"Authorization": f"Bearer {token}"}
    bytes_limit = int(data_gb) * 1024 * 1024 * 1024
    
    payload = {
        "username": username,
        "proxies": {
            "vless": {"flow": "xtls-rprx-vision"}, # طبق عکسی که فرستادی
            "vmess": {}
        },
        "data_limit": bytes_limit,
        "expire": 0, # بدون محدودیت زمانی طبق خواسته تو
        "status": "active"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{config.PANEL_URL}/api/user", json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                sub_url = data['subscription_url']
                
                # ذخیره لینک در دیتابیس برای دکمه "اشتراک‌های من"
                add_subscription(user_id, username, sub_url) 
                
                return sub_url
            else:
                print(f"Marzban API Error: {await resp.text()}")
                return None

async def renew_marzban_user(username, extra_gb):
    """افزودن حجم به کاربر فعلی (بدون تغییر در زمان)"""
    token = await get_marzban_token()
    if not token: return None
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        # ۱. دریافت حجم فعلی
        async with session.get(f"{config.PANEL_URL}/api/user/{username}", headers=headers) as resp:
            if resp.status != 200: return None
            user_data = await resp.json()
            
        current_limit = user_data.get('data_limit', 0)
        new_limit = current_limit + (int(extra_gb) * 1024 * 1024 * 1024)
        
        payload = {
            "data_limit": new_limit, 
            "expire": 0,
            "status": "active"
        }
        async with session.put(f"{config.PANEL_URL}/api/user/{username}", json=payload, headers=headers) as resp:
            return resp.status == 200

async def get_marzban_user_usage(username):
    """دریافت وضعیت مصرف حجم"""
    token = await get_marzban_token()
    if not token: return None
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{config.PANEL_URL}/api/user/{username}", headers=headers) as resp:
            if resp.status == 200:
                user_data = await resp.json()
                total = user_data.get('data_limit', 0)
                used = user_data.get('used_traffic', 0)
                
                total_gb = round(total / (1024**3), 2)
                used_gb = round(used / (1024**3), 2)
                remaining_gb = round(max(0, total_gb - used_gb), 2)
                
                return used_gb, remaining_gb, total_gb
            return None

# --- توابع کمکی ---

def generate_random_username():
    chars = string.ascii_lowercase + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(6))
    return f"Arad_{random_part}"

async def get_crypto_prices():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.nobitex.ir/v2/orderbook/USDTIRT") as resp:
                data = await resp.json()
                # تبدیل از ریال نوبیتکس به تومان
                tether_price = int(data['lastTradePrice']) / 10 
            return int(tether_price)
    except Exception as e:
        print(f"Price Error: {e}")
        return 70000