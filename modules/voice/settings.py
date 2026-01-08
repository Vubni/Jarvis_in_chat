from core import *
from config import jarvis_all, data_users
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton
from aiogram import Router, F
from database.functions import save_settings

router = Router()

NAME = "🔊 Аудио в ГС"
UNIQ_ID = "cVOICEv2"
PATH = "audio_converter"

@router.callback_query(F.data == UNIQ_ID)
async def modules(call: CallbackQuery):
    message = call.message
    item = jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH]
    inline_kb_list = [[IButton(text="🔴Не активен", callback_data=UNIQ_ID + "/start")]]
    
    if item:
        inline_kb_list = [[IButton(text="🟢Активен", callback_data=UNIQ_ID + "/stop")]]
    
    inline_kb_list.append([IButton(text="🌐Подробнее", url="https://vubni.gitbook.io/jarvis/besplatnaya-versiya/obychnye-komandy/sdelat-gs")])
    inline_kb_list.append([IButton(text="«", callback_data="commands")])
    
    await message.edit_text(
        "<b>🔊 Преобразование аудио в голосовые сообщения ✨</b>\n\n"
        "Ответь на любое аудиосообщение командой:\n"
        "<code>сделай гс</code>\n\n"
        "Бот автоматически конвертирует аудио в формат Telegram Voice Message!",
        reply_markup=IMarkup(inline_keyboard=inline_kb_list)
    )
    
@router.callback_query(F.data.startswith(UNIQ_ID))
async def modules(call: CallbackQuery):
    message = call.message
    data = call.data.replace(UNIQ_ID, "")
    
    if data == "/stop":
        jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH] = False
        inline_kb_list = [[IButton(text="🔴Не активен", callback_data=UNIQ_ID + "/start")]]
    else:
        jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH] = True
        inline_kb_list = [[IButton(text="🟢Активен", callback_data=UNIQ_ID + "/stop")]]
    
    await save_settings(call.from_user.id)
        
    inline_kb_list.append([IButton(text="🌐Подробнее", url="https://vubni.gitbook.io/jarvis/besplatnaya-versiya/obychnye-komandy/sdelat-gs")])
    inline_kb_list.append([IButton(text="«", callback_data="commands")])
    
    await message.edit_text(
        "<b>🔊 Преобразование аудио в голосовые сообщения ✨</b>\n\n"
        "Ответь на любое аудиосообщение командой:\n"
        "<code>сделай гс</code>\n\n"
        "Бот автоматически конвертирует аудио в голосовое сообщение!",
        reply_markup=IMarkup(inline_keyboard=inline_kb_list)
    )