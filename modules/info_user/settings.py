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

NAME = "📋Информация о человеке"
UNIQ_ID = "c4v1"
PATH = "info_user"


@router.callback_query(F.data == UNIQ_ID)
async def modules(call: CallbackQuery):
    message = call.message
    item = jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH]
    inline_kb_list = [[IButton(text="🔴Не активен", callback_data=UNIQ_ID + "/start")]]
    if item:
        inline_kb_list = [[IButton(text="🟢Активен", callback_data=UNIQ_ID + "/stop")]]
        
    inline_kb_list.append([IButton(text="🌐Подробнее", callback_data="test")])
    inline_kb_list.append([IButton(text="«", callback_data="commands")])
    await message.edit_text("<b>📋Информация о человеке позволяет вам узнать id аккаунта, получить вечную ссылку на него и посмотреть не было ли жалоб в системе Джарвиса! ✨</b>\n\nОтправьте в любом чате сообщение 'информация о @username' и получите всё, что нужно!\n\n<i>Обновление 2.0 - Работает и для групп</i>", reply_markup=IMarkup(inline_keyboard=inline_kb_list))
    
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
        
    inline_kb_list.append([IButton(text="🌐Подробнее", callback_data="test")])
    inline_kb_list.append([IButton(text="«", callback_data="commands")])
    await message.edit_text("<b>📋Информация о человеке позволяет вам узнать id аккаунта, получить вечную ссылку на него и посмотреть не было ли жалоб в системе Джарвиса! ✨</b>\n\nОтправьте в любом чате сообщение 'информация о @username' и получите всё, что нужно!\n\n<i>Обновление 2.0 - Работает и для групп</i>", reply_markup=IMarkup(inline_keyboard=inline_kb_list))