from json import load, dumps
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message

from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton

import keyboards.inline_kbs as kb

import functions.reg as func_reg
from database.database import Database
import config
from aiogram.types import ReplyKeyboardRemove as KRemove
from html import escape
from FSM import fsm

from create_bot import bot

router = Router()

# @router.message(F.text, fsm.Promo.create_1)
# async def Attention_edit_news(message: Message):
#     user_id = message.from_user.id
#     await fsm.delete_register(user_id)
#     try:
#         await fsm.set_data({"type": int(message.text)}, user_id)
#     except:
#         return
#     await message.answer("🛡️Администратор. Пожалуйста, выбери срок действия промокода", reply_markup=)