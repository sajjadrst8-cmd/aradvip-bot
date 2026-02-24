import aiohttp
import string
import random
import config
import time
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from loader import dp, bot

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

async def create_marzban_user(username, data_gb):
    """ساخت کاربر بدون محدودیت زمانی (expire=0)"""
    token = await get_marzban_token()
    if not token: return None
    
    headers = {"Authorization": f"Bearer {token}"}
    bytes_limit = int(data_gb) * 1024 * 1024 * 1024
    
    payload = {
        "username": username,
        "proxies": {"vless": {"flow": "xtls-rprx-vision"}, "vmess": {}},
        "inbounds": {"vless": []},
        "data_limit": bytes_limit,
        "expire": 0, # بدون محدودیت زمانی
        "status": "active"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{config.PANEL_URL}/api/user", json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data['subscription_url']
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
        # اضافه کردن حجم جدید به حجم قبلی
        new_limit = current_limit + (int(extra_gb) * 1024 * 1024 * 1024)
        
        payload = {
            "data_limit": new_limit, 
            "expire": 0, # اطمینان از نامحدود بودن زمان
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
                tether_price = int(data['lastTradePrice']) / 10 
            return int(tether_price)
    except:
        return 70000 
