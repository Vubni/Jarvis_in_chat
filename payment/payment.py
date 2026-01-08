from core import time_now, strftime, strptime
from database.database import Database

import json
from dateutil.relativedelta import relativedelta

from aiogram.types import Message, PreCheckoutQuery
from aiogram import Router, F
from config import jarvis_all, data_users
from FSM import fsm
from config import logger
from datetime import datetime

router_payment = Router()


@router_payment.pre_checkout_query(lambda query: True)
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    try:
        await pre_checkout_query.answer(ok=True)
    except Exception as e:
        print(f"Ошибка в pre_checkout_query_handler: {e}")
        await pre_checkout_query.answer(ok=False, error_message="Что-то пошло не так. Пожалуйста, попробуйте снова.")

            
@router_payment.message(F.successful_payment)
async def successful_payment(message: Message):
    user_id = message.from_user.id
    try:
        data = await fsm.get_data(user_id)
        data = data if data else []
    except Exception as e:
        logger.error(f"Ошибка при получении данных FSM: {e}")
        data = []

    async with Database() as db:
        try:
            if "promo_code" in data:
                await db.execute("UPDATE promo_codes SET count=count-1 WHERE code=$1", (data["promo_code"],))
                await db.execute("DELETE FROM promo_codes WHERE count <= 0")

            params = message.successful_payment.invoice_payload.split("|")
            if len(params) != 5:
                return logger.error("Неверный формат invoice_payload", params)

            # Обработка даты с явным форматом
            now = datetime.now()
            end_time_subscription = now + relativedelta(months=int(params[2]))
            subscription = (await db.execute("SELECT subscription FROM profiles WHERE user_id=$1", (user_id,)))['subscription']

            if subscription:
                # Парсинг и форматирование с явным форматом
                paid_before = datetime.strptime(subscription["paid_before"], "%Y-%m-%d")
                paid_before += relativedelta(months=int(params[2]))
                subscription.update({
                    "charge_id": message.successful_payment.telegram_payment_charge_id,
                    "paid_before": paid_before.strftime("%Y-%m-%d"),
                    "subscription": {"status": True} if bool(params[4]) and not bool(params[3]) else {"status": False}
                })
            else:
                result = {
                    "charge_id": message.successful_payment.telegram_payment_charge_id,
                    "type": params[0],
                    "date_subscription": now.strftime("%Y-%m-%d"),
                    "paid_before": (now + relativedelta(months=int(params[2]))).strftime("%Y-%m-%d"),
                    "by_price": int(params[1]),
                    "is_stock": bool(params[3]),
                    "subscription": {"status": True} if bool(params[4]) and not bool(params[3]) else {"status": False}
                }

            await db.execute("UPDATE profiles SET subscription=$1 WHERE user_id=$2", (json.dumps(result), user_id))
            await db.close_connection()
            await jarvis_all[data_users[user_id]].update_subscription()
        
        except Exception as e:
            logger.error(f"Ошибка при обработке платежа: {e}")
            raise

    # Отправка сообщения пользователю
    await message.answer(
        f"Успешно! Подписка оформлена до {end_time_subscription.strftime('%d.%m.%Y')}\nПриятного использования подписки💖",
        parse_mode="Markdown",
        message_effect_id="5046509860389126442"
    )