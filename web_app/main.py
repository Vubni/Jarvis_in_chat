from aiogram import Router, F
from aiogram.types import Message, WebAppData
from aiogram.filters import Command
import json
import logging
from config import jarvis_all, data_users
from database.database import Database
from aiogram.types import ReplyKeyboardRemove as KRemove
import keyboards.inline_kbs as kb


router_web_app = Router()

@router_web_app.message(F.web_app_data)
async def handle_webapp_data(message: Message):  # Remove the web_app_data parameter
    try:
        web_app_data = message.web_app_data
        access_token = web_app_data.data
        
        if len(access_token) < 10:
            await message.answer("Неверные данные!")
            return
        
        jarvis_all[data_users[message.chat.id]].yandex_token = access_token
        async with Database() as db:
            await db.execute("INSERT INTO smart_home (user_id, yandex_token) VALUES ($1, $2)", (message.chat.id, access_token))
        await message.reply("<b>Яндекс аккаунт успешно привязан✅</b>\n🏠Управление умным домом доступно.", reply_markup=KRemove())
        return await message.answer("Привет👋\nНастройки и список команд бота:", reply_markup=kb.main())
    except json.JSONDecodeError:
        await message.answer("Ошибка обработки данных", reply_markup=KRemove())
    except Exception as e:
        logging.error(e)
        await message.answer("Произошла ошибка", reply_markup=KRemove())