import os, datetime
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL")
cluster = AsyncIOMotorClient(MONGO_URL)
db = cluster["arad_database"]
users_col = db["users"]
invoices_col = db["invoices"]
plans_col = db["plans"]

async def get_user(user_id, referrer_id=None):
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        new_user = {
            "user_id": user_id,
            "wallet": 0,           # موجودی به تومان
            "usdt_balance": 0,     # موجودی تتر (اختیاری)
            "trx_balance": 0,      # موجودی ترون (اختیاری)
            "ref_count": 0,
            "referred_by": referrer_id,
            "reg_date": datetime.datetime.now()
        }
        await users_col.insert_one(new_user)
        # ... باقی کدها

        # اگر معرف داشت، تعداد زیرمجموعه‌های معرف را یکی زیاد کن
        if referrer_id:
            await users_col.update_one({"user_id": int(referrer_id)}, {"$inc": {"ref_count": 1}})
            
        return new_user
    return user

async def add_invoice(user_id, data):
    inv_id = os.urandom(8).hex() # شناسه رندوم
    invoice = {
        "inv_id": inv_id,
        "user_id": user_id,
        "status": "🟠 در انتظار",
        "amount": data['price'],
        "type": data['type'],
        "plan": data['plan'],
        "username": data.get('username', '-'),
        "date": datetime.datetime.now().strftime("%Y/%m/%d - %H:%M")
    }
    await invoices_col.insert_one(invoice)
    return invoice

# این کدها را به انتهای فایل database.py اضافه کن
async def is_duplicate_receipt(file_unique_id):
    # چک کردن در کالکشنی به نام receipts (در صورتی که نباشد خودکار ساخته می‌شود)
    receipts_col = db['receipts'] # فرض بر این است که متغیر db در این فایل تعریف شده
    exists = await receipts_col.find_one({"file_id": file_unique_id})
    return True if exists else False

async def save_receipt(file_unique_id, user_id):
    receipts_col = db['receipts']
    await receipts_col.insert_one({
        "file_id": file_unique_id,
        "user_id": user_id,
        "date": datetime.datetime.now()
    })
