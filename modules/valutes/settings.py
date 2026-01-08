from core import *
from config import jarvis_all, data_users
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton
from aiogram import Router, F
from database.functions import save_settings

router = Router()

NAME = "💱 Валюты"
UNIQ_ID = "cCURRENCY"
PATH = "currency"

@router.callback_query(F.data == UNIQ_ID)
async def currency_settings(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    user_settings = jarvis_all[data_users[user_id]].settings["modules"].get(PATH, {})
    
    inline_kb = []
    
    # Кнопка активации модуля
    status_btn = IButton(
        text=f"{'🟢' if user_settings.get('status', False) else '🔴'} Модуль: {'Вкл' if user_settings.get('status', False) else 'Выкл'}",
        callback_data=f"{UNIQ_ID}/toggle_module"
    )
    inline_kb.append([status_btn])
    
    # Кнопка авто-конвертации
    auto_btn = IButton(
        text=f"{'🔄' if user_settings.get('status_auto', False) else '⏹️'} Автоконвертация: {'Вкл' if user_settings.get('status_auto', False) else 'Выкл'}",
        callback_data=f"{UNIQ_ID}/toggle_auto"
    )
    inline_kb.append([auto_btn])
    
    # Информационная кнопка
    info_btn = IButton(
        text="📚 Подробнее",
        url="https://vubni.gitbook.io/jarvis/besplatnaya-versiya/obychnye-komandy/kurs-valyut"
    )
    inline_kb.append([info_btn])
    
    # Кнопка возврата
    back_btn = IButton(text="« Назад", callback_data="commands")
    inline_kb.append([back_btn])
    
    await message.edit_text(
        "<b>💱 Модуль валют ✨</b>\n\n"
        "Функции:\n"
        "• <code>курс [валюта]</code> - показать актуальный курс\n"
        "• Автоматическая конвертация сумм в сообщениях\n\n"
        "Поддержка:\n"
        " Fiat: 💸 USD, EUR, RUB, THB, GBP, JPY, CHF, CNY, TRY\n"
        " Crypto: 🔥 BTC, ETH, TON, LTC, XRP, ADA, SOL, DOGE",
        reply_markup=IMarkup(inline_keyboard=inline_kb)
    )

@router.callback_query(F.data.startswith(f"{UNIQ_ID}/"))
async def handle_currency_actions(call: CallbackQuery):
    user_id = call.from_user.id
    action = call.data.split('/')[-1]
    
    # Инициализация настроек при первом использовании
    if PATH not in jarvis_all[data_users[user_id]].settings["modules"]:
        jarvis_all[data_users[user_id]].settings["modules"][PATH] = {
            "status": False,
            "status_auto": False
        }
    
    settings = jarvis_all[data_users[user_id]].settings["modules"][PATH]
    
    if action == "toggle_module":
        settings["status"] = not settings["status"]
    elif action == "toggle_auto":
        settings["status_auto"] = not settings["status_auto"]
    
    await save_settings(user_id)
    await currency_settings(call)