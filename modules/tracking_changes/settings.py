from core import *
import config
from config import jarvis_all, data_users
from json import dumps

from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton
from aiogram import Router, F
from database.database import Database
from database.functions import save_settings

router = Router()

NAME = "🔍Отслеж. изменений"
UNIQ_ID = "c11v1"
PATH = "tracking_changes"


@router.callback_query(F.data == UNIQ_ID)
async def modules(call: CallbackQuery):
    message = call.message
    item = jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH]
    inline_kb_list = [[IButton(text="🔴Не активен", callback_data=UNIQ_ID + "/start")]]
    if item:
        inline_kb_list = [[IButton(text="🟢Активен", callback_data=UNIQ_ID + "/stop")]]
        
    inline_kb_list.append([IButton(text="🌐Подробнее", url="https://vubni.gitbook.io/jarvis/besplatnaya-versiya/unikalnye-vozmozhnosti/uvedomlenie-pri-poyavlenii-v-seti")])
    inline_kb_list.append([IButton(text="«", callback_data="commands")])
    await message.edit_text("<b>🔍Отслеживание изменений позволяет отслеживать любые изменения, например появление человека в сети, прочтение сообщения, изменение автарки и т.д.!</b>", reply_markup=IMarkup(inline_keyboard=inline_kb_list))
    
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
        
    inline_kb_list.append([IButton(text="🌐Подробнее", url="https://vubni.gitbook.io/jarvis/besplatnaya-versiya/unikalnye-vozmozhnosti/uvedomlenie-pri-poyavlenii-v-seti")])
    inline_kb_list.append([IButton(text="«", callback_data="commands")])
    await message.edit_text("<b>🔍Отслеживание изменений позволяет отслеживать любые изменения, например появление человека в сети, прочтение сообщения, изменение автарки и т.д.!</b>", reply_markup=IMarkup(inline_keyboard=inline_kb_list))