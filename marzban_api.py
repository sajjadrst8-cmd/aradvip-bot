# marzban_api.py
import requests
from config import MARZBAN_USERNAME, MARZBAN_PASSWORD, MARZBAN_API_URL

class MarzbanAPI:
    def __init__(self):
        self.base_url = MARZBAN_API_URL
        self.token = None
        self.login()

    def login(self):
        """
        ورود به Marzban با یوزرنیم و پسورد
        و گرفتن access_token
        """
        url = f"{self.base_url}/auth/login"  # endpoint ورود
        payload = {
            "username": MARZBAN_USERNAME,
            "password": MARZBAN_PASSWORD
        }
        try:
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            self.token = data.get("access_token")
            if not self.token:
                raise Exception("توکن دریافت نشد!")
            print("ورود به Marzban موفقیت‌آمیز بود ✅")
        except requests.exceptions.RequestException as e:
            print("خطا در ورود به Marzban:", e)
        except Exception as e:
            print(e)

    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get_subscriptions(self):
        """
        گرفتن لیست اشتراک‌های فعال
        """
        url = f"{self.base_url}/subscriptions"
        try:
            resp = requests.get(url, headers=self.headers())
            resp.raise_for_status()
            return resp.json()  # لیست اشتراک‌ها
        except requests.exceptions.RequestException as e:
            print("خطا در گرفتن اشتراک‌ها:", e)
            return []

    def buy_subscription(self, user_id, subscription_id):
        """
        خرید اشتراک جدید
        user_id: آی‌دی تلگرام کاربر
        subscription_id: شناسه اشتراک
        """
        url = f"{self.base_url}/subscriptions/buy"
        payload = {
            "user_id": user_id,
            "subscription_id": subscription_id
        }
        try:
            resp = requests.post(url, json=payload, headers=self.headers())
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            print("خطا در خرید اشتراک:", e)
            return {"ok": False, "error": str(e)}