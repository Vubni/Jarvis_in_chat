from aiogram import Router, F

import keyboards.settings_chats as kb

from database.functions import save_settings
from aiogram.types import ReplyKeyboardRemove as KRemove
from aiogram.types import CallbackQuery
from FSM import fsm

from config import data_users, jarvis_all

router_call_settings_chats = Router()

@router_call_settings_chats.callback_query(F.data == 'monitored')
async def monitored(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await fsm.delete_register(user_id)
    await (await message.answer("Удаление кнопки...", reply_markup=KRemove())).delete()
    await message.edit_text("🌟 Здесь вы можете включить или выключить отслеживание изменений и удалений сообщений, а также активировать или деактивировать команды Джарвиса в различных группах, личных чатах и даже каналах! 💬\n\n"
                            "🔒 Кроме того, вы можете добавить исключения для личных чатов, групп и каналов, чтобы Джарвис, работал только там, где нужно!", reply_markup=kb.monitored())
    
@router_call_settings_chats.callback_query(F.data == 'monitored_chats')
async def monitored_chats(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await message.edit_text("Настройки для доступа Джарвис к личным чатам:", reply_markup=kb.monitored_chats(user_id))

@router_call_settings_chats.callback_query(F.data == 'monitored_groups')
async def monitored_groups(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await message.edit_text("Настройки для доступа Джарвис к группам:", reply_markup=kb.monitored_groups(user_id))

@router_call_settings_chats.callback_query(F.data.startswith('chats_'))
async def chats_off(call: CallbackQuery):
    user_id = call.from_user.id
    temp = {"off": False, "on": True}
    status = temp[call.data.split("_")[1]]
    type_status = call.data.split("_")[2]
    jarvis_all[data_users[user_id]].settings["chats"][type_status] = status
    await save_settings(user_id)
    await monitored_chats(call)

@router_call_settings_chats.callback_query(F.data.startswith('groups_'))
async def groups_off(call: CallbackQuery):
    user_id = call.from_user.id
    temp = {"off": False, "on": True}
    status = temp[call.data.split("_")[1]]
    type_status = call.data.split("_")[2]
    jarvis_all[data_users[user_id]].settings["groups"][type_status] = status
    await save_settings(user_id)
    await monitored_groups(call)

@router_call_settings_chats.callback_query(F.data == "except_chats")
async def except_chats(call: CallbackQuery):
    user_id = call.from_user.id
    message = call.message
    subscription = jarvis_all[data_users[user_id]].subscription
    text = f"""🌟 Индивидуальные настройки чатов 🌟

Здесь вы можете добавить <b>{"до 2" if not subscription else "любое количество"}</b> чатов, к которым будут применяться индивидуальные настройки. ✨

Примеры возможностей:

🚫 Полностью отключите работу Джарвиса для определённого чата.
✅ Или, наоборот, включите его, несмотря на основные настройки!"""
    await message.answer("Создание кнопки . . .", reply_markup=kb.new_except(user_id))
    await fsm.register_next(fsm.Chats_settings.chats_except, user_id)
    await message.edit_text(text, reply_markup=await kb.excepts_all(user_id))

@router_call_settings_chats.callback_query(F.data.startswith("except|"))
async def chats_settings(call: CallbackQuery):
    user_id = call.from_user.id
    message = call.message
    id_chat = int(call.data.replace("except|", ""))
    name = await jarvis_all[data_users[user_id]].get_title_or_name(jarvis_all[data_users[user_id]].settings["func_except"][id_chat]["id"])
    await message.edit_text(f"Настройки для доступа Джарвис к чату {name}", reply_markup=kb.settings_except(id_chat, user_id))

@router_call_settings_chats.callback_query(F.data.startswith("except_delete_"))
async def delete_chat(call: CallbackQuery):
    user_id = call.from_user.id
    id_chat = int(call.data.replace("except_delete_", ""))
    del jarvis_all[data_users[user_id]].settings["func_except"][id_chat]
    await save_settings(user_id)
    await except_chats(call)

@router_call_settings_chats.callback_query(F.data.startswith('except_'))
async def chats_off(call: CallbackQuery):
    user_id = call.from_user.id
    message = call.message
    temp = {"off": False, "on": True}
    status = temp[call.data.split("_")[1]]
    type_status = call.data.split("_")[2]
    id_chat = int(call.data.split("_")[3])
    jarvis_all[data_users[user_id]].settings["func_except"][id_chat][type_status] = status
    await save_settings(user_id)
    name = await jarvis_all[data_users[user_id]].get_title_or_name(jarvis_all[data_users[user_id]].settings["func_except"][id_chat]["id"])
    await message.edit_text(f"Настройки для доступа Джарвис к чату {name}", reply_markup=kb.settings_except(id_chat, user_id))