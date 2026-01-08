from json import load, dumps
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message

import keyboards.inline_kbs as kb

import functions.reg as func_reg
from database.database import Database
import config
from aiogram.types import ReplyKeyboardRemove as KRemove
from aiogram.types import CallbackQuery
from FSM import fsm

from config import data_users, jarvis_all

from functions import offers

router_call_offers = Router()

@router_call_offers.callback_query(F.data == 'suggest_idea')
async def suggest_idea(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await message.edit_text("📩 Пожалуйста, отправьте название и описание вашего предложения в следующем формате:\n\nДобавьте антиспам\nДобавьте антиспам, чтобы он блокировал чаты, если он...", 
                            reply_markup=kb.back("offers"))
    fsm.register_next(fsm.Suggest_idea.suggest, user_id)

