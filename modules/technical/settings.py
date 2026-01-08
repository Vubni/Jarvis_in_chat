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

NAME = "⚙️Тех. команды"
UNIQ_ID = "c6v1"
PATH = "technical"


@router.callback_query(F.data == UNIQ_ID)
async def modules(call: CallbackQuery):
    message = call.message
    inline_kb_list = []
    inline_kb_list.append([IButton(text="🌐Подробнее", url="https://vubni.gitbook.io/jarvis/besplatnaya-versiya/tekhnichesie-komandy")])
    inline_kb_list.append([IButton(text="«", callback_data="commands")])
    await message.edit_text("<b>⚙️Технические команды являются обязательными и их невозможно выключить, они позволяют отследить статус работы Джарвиса! ✨</b>\n\nОтправьте в любом чате сообщение 'пинг' и Джарвис сообщит техническую информацию.", reply_markup=IMarkup(inline_keyboard=inline_kb_list))