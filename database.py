import os, datetime
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL")
cluster = AsyncIOMotorClient(MONGO_URL)
db = cluster["arad_database"]
users_col = db["users"]
invoices_col = db["invoices"]
plans_col = db["plans"]

async def get_user(user_id, referrer=None):
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        user = {
            "user_id": user_id,
            "wallet": 0,
            "referred_by": int(referrer) if (referrer and str(referrer).isdigit() and int(referrer) != user_id) else None,
            "join_date": datetime.datetime.now().strftime("%Y/%m/%d - %H:%M"),
            "test_used": {"v2ray": False, "biubiu": False}
        }
        await users_col.insert_one(user)
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
