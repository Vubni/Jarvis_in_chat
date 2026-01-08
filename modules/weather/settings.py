from core import *
import config
from config import jarvis_all, data_users
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton
from aiogram import Router, F
from database.database import Database
from database.functions import save_settings

router = Router()

NAME = "🌤 Погода"
UNIQ_ID = "cWeath"
PATH = "weather"

@router.callback_query(F.data == UNIQ_ID)
async def weather_settings(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    current_status = jarvis_all[data_users[user_id]].settings["modules"][PATH]
    
    # Создаем кнопку состояния
    status_button = [
        [IButton(text="🟢 Активен" if current_status else "🔴 Не активен",
                 callback_data=f"{UNIQ_ID}/toggle")]
    ]
    
    # Добавляем дополнительные кнопки
    keyboard = status_button + [
        [IButton(text="🌐 Подробнее", 
                 url="https://vubni.gitbook.io/jarvis/besplatnaya-versiya/obychnye-komandy/pogoda")],
        [IButton(text="« Назад", callback_data="commands")]
    ]
    
    await message.edit_text(
        "<b>🌤 Модуль погоды позволяет узнавать текущую погоду в любом городе!✨</b>",
        reply_markup=IMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(F.data.startswith(f"{UNIQ_ID}/toggle"))
async def toggle_weather(call: CallbackQuery):
    user_id = call.from_user.id
    current_status = jarvis_all[data_users[user_id]].settings["modules"][PATH]
    
    # Инвертируем состояние
    new_status = not current_status
    jarvis_all[data_users[user_id]].settings["modules"][PATH] = new_status
    
    # Сохраняем настройки в БД
    await save_settings(user_id)
    
    # Обновляем интерфейс
    await weather_settings(call)