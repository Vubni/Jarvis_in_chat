from core import *
from config import jarvis_all, data_users
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton
from aiogram import Router, F
from database.functions import save_settings

router = Router()

NAME = "🌐 Переводчик"
UNIQ_ID = "сTRANSLATE"
PATH = "translator"

@router.callback_query(F.data == UNIQ_ID)
async def translation_settings(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    settings = jarvis_all[data_users[user_id]].settings["modules"]
    is_active = settings.get(PATH, False)
    
    inline_kb = []
    status_btn = IButton(
        text="🟢 Активен" if is_active else "🔴 Не активен",
        callback_data=f"{UNIQ_ID}/{'stop' if is_active else 'start'}"
    )
    inline_kb.append([status_btn])
    
    info_button = IButton(
        text="🌐 Подробнее", 
        url="https://vubni.gitbook.io/jarvis/besplatnaya-versiya/obychnye-komandy/kurs-valyut"
    )
    back_button = IButton(text="« Назад", callback_data="commands")
    inline_kb.append([info_button])
    inline_kb.append([back_button])
    
    await message.edit_text(
        "<b>🌐 Модуль перевода ✨</b>\n\n"
        "Используйте команды:\n"
        "<code>переведи [на язык] [текст]</code>\n"
        "или ответьте на сообщение командой <code>переведи</code>\n\n"
        "Поддержка 12 языков: русский, английский, французский, немецкий, испанский и другие.",
        reply_markup=IMarkup(inline_keyboard=inline_kb)
    )

@router.callback_query(F.data.startswith(f"{UNIQ_ID}/"))
async def toggle_translation(call: CallbackQuery):
    user_id = call.from_user.id
    action = call.data.split('/')[-1]
    
    settings = jarvis_all[data_users[user_id]].settings["modules"]
    settings[PATH] = (action == 'start')
    
    await save_settings(user_id)
    await translation_settings(call)