from core import *
from config import jarvis_all, data_users
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton
from aiogram import Router, F
from database.functions import save_settings

router = Router()

NAME = "🛡 Управление группой"
UNIQ_ID = "mGROUP_ADMIN"
PATH = "group_management"

@router.callback_query(F.data == UNIQ_ID)
async def modules(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    item = jarvis_all[data_users[user_id]].settings["modules"][PATH]
    if not jarvis_all[data_users[user_id]].subscription:
        return call.answer("🔐Доступно только для обладателей платной подписки!")
    
    status_btn = IButton(text="🔴Не активен", callback_data=f"{UNIQ_ID}/start")
    if item:
        status_btn = IButton(text="🟢Активен", callback_data=f"{UNIQ_ID}/stop")
    
    markup = IMarkup(inline_keyboard=[
        [status_btn],
        [IButton(text="🌐Документация", url="https://vubni.gitbook.io/jarvis/")],
        [IButton(text="« Назад", callback_data="commands")]
    ])
    
    await message.edit_text(
        "<b>🛡 Модуль управления группой</b>\n\n"
        "Команды для администраторов:\n"
        "<code>бан</code> - заблокировать пользователя\n"
        "<code>мут</code> - ограничить отправку сообщений\n"
        "<code>кик</code> - удалить участника\n"
        "<code>общий сбор</code> - массовое упоминание\n\n"
        "Требуются права администратора в чате",
        reply_markup=markup
    )

@router.callback_query(F.data.startswith(UNIQ_ID))
async def toggle_module(call: CallbackQuery):
    user_id = call.from_user.id
    action = call.data.split('/')[-1]
    
    if action == "stop":
        jarvis_all[data_users[user_id]].settings["modules"][PATH] = False
    else:
        jarvis_all[data_users[user_id]].settings["modules"][PATH] = True
    
    await save_settings(user_id)
    await modules(call)  # Обновляем отображение после изменения