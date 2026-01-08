from database.database import Database
import json
from core import *
from create_bot import bot
from datetime import datetime


async def referal_gift(user_id, user_id2):
    now = datetime.now(pytz.UTC)
    subscription = {"charge_id": "",
            "type": "Pro",
            "date_subscription": strftime(now.date()),
            "paid_before": strftime((now + timedelta(days=5)).date()),
            "by_price": 0,
            "is_stock": True,
            "subscription": False}
    async with Database() as db:
        await db.execute("UPDATE profiles SET subscription=$1 WHERE user_id=$2", (subscription, user_id))
        info = await db.execute("SELECT * FROM profiles WHERE user_id=$1", (user_id2,))
        if not info["subscription"]:
            await db.execute("UPDATE profiles SET subscription=$1 WHERE user_id=$2", (subscription, user_id2))
            await bot.send_message(user_id2, f"<b>По вашей реферальной ссылке зарегистрировался {user.first_name}!</b>\nВам была выдана подписка Pro на 5 дней!")
        else:
            subscription = info["subscription"]
            bonus = {"Pro" : 5, "Бизнес": 2}
            subscription["paid_before"] = strftime(strptime(subscription["paid_before"]) + timedelta(days=bonus[subscription["type"]]))
            await db.execute("UPDATE profiles SET subscription=$1 WHERE user_id=$2", (subscription, user_id2))
            if subscription["type"] == "Pro":
                await bot.send_message(user_id2, f"<b>По вашей реферальной ссылке зарегистрировался {user.first_name}!</b>\nВаша подписка была продлена на 5 дней!")
            else:
                await bot.send_message(user_id2, f"<b>По вашей реферальной ссылке зарегистрировался {user.first_name}!</b>\nВаша подписка была продлена на 2 дня!")
    await bot.send_message(user_id, "<b>Реферальная программа успешно активирована!</b>\nВам была выдана подписка Pro на 5 дней!")
    user = await bot.get_chat(user_id)


async def register_func(user_id, phone):
    async with Database() as db:
        result = await db.execute("SELECT * FROM profiles WHERE user_id=$1", (user_id,))
        if result:
            if result["phone"] == None:
                await db.execute("UPDATE profiles SET phone=$1, status=true WHERE id=$2", (phone, result["id"]))
                await referal_gift(user_id, result["referal"])
            if result["status"] == 0:
                await db.execute("UPDATE profiles SET status=true, reason=NULL WHERE id=$1", (result["id"],))
        else:
            settings = json.load(open('./base_settings/base_settings.json', 'r', encoding='utf-8'))
            await db.execute("INSERT INTO profiles (phone, user_id, settings) VALUES ($1, $2, $3)", (phone, user_id, json.dumps(settings)))

@cache_with_expiration(5)
async def check_registration_user(user_id: int) -> bool:
    async with Database() as db:
        return bool(await db.execute("SELECT user_id FROM profiles WHERE user_id=$1 AND status=true", (user_id,)))


@cache_with_expiration(60)
async def check_pro(user_id: int) -> bool:
    async with Database() as db:
        return bool(await db.execute("SELECT user_id FROM profiles WHERE user_id=$1 and subscription->>'type' = 'Pro'", (user_id,)))


@cache_with_expiration(60)
async def check_business(user_id: int) -> bool:
    async with Database() as db:
        return bool(await db.execute("SELECT user_id FROM profiles WHERE user_id=$1 AND subscription->>'type' = 'Бизнес'", (user_id,)))
    
@cache_with_expiration(60)
async def check_admin(user_id: int, level=1) -> bool:
    async with Database() as db:
        return bool(await db.execute("SELECT user_id FROM admins WHERE user_id=$1 AND level >= $2", (user_id, level)))
    
@cache_with_expiration(60)
async def get_admin(user_id: int) -> bool:
    async with Database() as db:
        return (await db.execute("SELECT level FROM admins WHERE user_id=$1", (user_id,)))["level"]