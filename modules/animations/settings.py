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

NAME = "💫Анимации"
UNIQ_ID = "c10v1"
PATH = "animations"


@router.callback_query(F.data == UNIQ_ID)
async def modules(call: CallbackQuery):
    message = call.message
    item = jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH]["status"]
    status_animate = True
    if item:
        inline_kb_list = [[IButton(text="🟢Активен", callback_data=UNIQ_ID + "/stop")]]
    else:
        inline_kb_list = [[IButton(text="🔴Не активен", callback_data=UNIQ_ID + "/start")]]
        status_animate = False
    if status_animate:
        #взаимодействие с анимацией (магия)
        item = jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH]["magic"]
        if item:
            inline_kb_list.append([IButton(text="🟢Магия", callback_data=UNIQ_ID + "/01/stop")])
        else:
            inline_kb_list.append([IButton(text="🔴Магия", callback_data=UNIQ_ID + "/01/start")])
        #взаимодействие с анимацией (сердечки)
        item = jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH]["heart"]
        if item:
            inline_kb_list.append([IButton(text="🟢Сердечко", callback_data=UNIQ_ID + "/02/stop")])
        else:
            inline_kb_list.append([IButton(text="🔴Сердечко", callback_data=UNIQ_ID + "/02/start")])

    inline_kb_list.append([IButton(text="🌐Подробнее", callback_data="test")])
    inline_kb_list.append([IButton(text="«", callback_data="commands")])
    await message.edit_text("<b>💫Анимации позволяют запускать красивые анимации в сообщениях!✨</b>", reply_markup=IMarkup(inline_keyboard=inline_kb_list))
    
@router.callback_query(F.data.startswith(UNIQ_ID))
async def modules(call: CallbackQuery):
    message = call.message
    data = call.data.replace(UNIQ_ID, "")
    status_animate = True
    if data == "/stop":
        jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH]["status"] = False
        inline_kb_list = [[IButton(text="🔴Не активен", callback_data=UNIQ_ID + "/start")]]
        status_animate = False
    elif data == "/start":
        jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH]["status"] = True
        inline_kb_list = [[IButton(text="🟢Активен", callback_data=UNIQ_ID + "/stop")]]
    else:
        item = jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH]["status"]
        if item:
            inline_kb_list = [[IButton(text="🟢Активен", callback_data=UNIQ_ID + "/stop")]]
        else:
            inline_kb_list + [[IButton(text="🔴Не активен", callback_data=UNIQ_ID + "/start")]]
            status_animate = False
    
    if status_animate:
        if data == "/01/stop":
            jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH]["magic"] = False
            inline_kb_list.append([IButton(text="🔴Магия", callback_data=UNIQ_ID + "/01/start")])
        elif data == "/01/start":
            jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH]["magic"] = True
            inline_kb_list.append([IButton(text="🟢Магия", callback_data=UNIQ_ID + "/01/stop")])
        else:
            item = jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH]["magic"]
            if item:
                inline_kb_list.append([IButton(text="🟢Магия", callback_data=UNIQ_ID + "/01/stop")])
            else:
                inline_kb_list.append([IButton(text="🔴Магия", callback_data=UNIQ_ID + "/01/start")])

        if data == "/02/stop":
            jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH]["heart"] = False
            inline_kb_list.append([IButton(text="🔴Сердечко", callback_data=UNIQ_ID + "/01/start")])
        elif data == "/02/start":
            jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH]["heart"] = True
            inline_kb_list.append([IButton(text="🟢Сердечко", callback_data=UNIQ_ID + "/01/stop")])
        else:
            item = jarvis_all[data_users[call.from_user.id]].settings["modules"][PATH]["heart"]
            if item:
                inline_kb_list.append([IButton(text="🟢Сердечко", callback_data=UNIQ_ID + "/02/stop")])
            else:
                inline_kb_list.append([IButton(text="🔴Сердечко", callback_data=UNIQ_ID + "/02/start")])

    
    await save_settings(call.from_user.id)
        
    inline_kb_list.append([IButton(text="🌐Подробнее", callback_data="test")])
    inline_kb_list.append([IButton(text="«", callback_data="commands")])
    await message.edit_text("<b>💫Анимации позволяют запускать красивые анимации в сообщениях!✨</b>", reply_markup=IMarkup(inline_keyboard=inline_kb_list))