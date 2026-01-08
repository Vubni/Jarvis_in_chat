from aiogram import Router, F
from aiogram.types import CallbackQuery

router_call_other = Router()

@router_call_other.callback_query(F.data)
async def other(call: CallbackQuery):
    print("Потерянные данные: ", call.data)