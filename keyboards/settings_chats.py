from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton
from aiogram.types import KeyboardButton as KButton
from aiogram.types import ReplyKeyboardMarkup as RMarkup
from aiogram.types import KeyboardButtonRequestUser as KUser
from aiogram.types import KeyboardButtonRequestChat as KChat

import config
from config import jarvis_all, data_users

def monitored():
    inline_kb_list = [[IButton(text="💬Личные чаты", callback_data="monitored_chats")],
    [IButton(text="👥Группы", callback_data="monitored_groups")],
    [IButton(text="📣Каналы", callback_data="test")],
    [IButton(text="⚙Индивидуальные настройки", callback_data="except_chats")],
    [IButton(text="«", callback_data="page")]]
    return IMarkup(inline_keyboard=inline_kb_list)

def monitored_chats(user_id):
    inline_kb_list = []
    if jarvis_all[data_users[user_id]].settings["chats"]["del"]:
        inline_kb_list.append([IButton(text='🟢Отслеживание удалений сообщ.', callback_data='chats_off_del')])
    else:
        inline_kb_list.append([IButton(text='🔴Отслеживание удалений сообщ.', callback_data='chats_on_del')])
    if jarvis_all[data_users[user_id]].settings["chats"]["edit"]:
        inline_kb_list.append([IButton(text='🟢Отслеживание изменений сообщ.', callback_data='chats_off_edit')])
    else:
        inline_kb_list.append([IButton(text='🔴Отслеживание изменений сообщ.', callback_data='chats_on_edit')])
    if jarvis_all[data_users[user_id]].settings["chats"]["command"]:
        inline_kb_list.append([IButton(text='🟢Работа команд', callback_data='chats_off_command')])
    else:
        inline_kb_list.append([IButton(text='🔴Работа команд', callback_data='chats_on_command')])
    inline_kb_list.append([IButton(text='«', callback_data='monitored')])
    return IMarkup(inline_keyboard=inline_kb_list)

def monitored_groups(user_id):
    inline_kb_list = []
    if jarvis_all[data_users[user_id]].settings["groups"]["del"]:
        inline_kb_list.append([IButton(text='🟢Отслеживание удалений сообщ.', callback_data='groups_off_del')])
    else:
        inline_kb_list.append([IButton(text='🔴Отслеживание удалений сообщ.', callback_data='groups_on_del')])
    if jarvis_all[data_users[user_id]].settings["groups"]["edit"]:
        inline_kb_list.append([IButton(text='🟢Отслеживание изменений сообщ.', callback_data='groups_off_edit')])
    else:
        inline_kb_list.append([IButton(text='🔴Отслеживание изменений сообщ.', callback_data='groups_on_edit')])
    if jarvis_all[data_users[user_id]].settings["groups"]["command"]:
        inline_kb_list.append([IButton(text='🟢Работа команд', callback_data='groups_off_command')])
    else:
        inline_kb_list.append([IButton(text='🔴Работа команд', callback_data='groups_on_command')])
    inline_kb_list.append([IButton(text='«', callback_data='monitored')])
    return IMarkup(inline_keyboard=inline_kb_list)

def new_except(user_id):
    subscription = jarvis_all[data_users[user_id]].subscription
    keyboard = []
    number = 1
    if not subscription:
        number = config.LIMIT_CHATS_EXCEPT-len(jarvis_all[data_users[user_id]].settings["func_except"])
    if number > 0:
        keyboard = [[KButton(text="💭Настроить личный чат", request_user=KUser(request_id=0, user_is_bot=False))]]
        if subscription:
            keyboard.append([KButton(text="👥Настроить группу", request_chat=KChat(request_id=1, chat_is_channel=False))])
    return RMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)

async def excepts_all(user_id):
    inline_kb_list = []
    indx = 0
    for item in jarvis_all[data_users[user_id]].settings["func_except"]:
        name = await jarvis_all[data_users[user_id]].get_title_or_name(item["id"])
        inline_kb_list.append([IButton(text=f'⚙Настроить {name}', callback_data=f'except|{indx}')])
        indx += 1
    inline_kb_list.append([IButton(text='«', callback_data='monitored')])
    return IMarkup(inline_keyboard=inline_kb_list)

def settings_except(id_chat, user_id):
    if jarvis_all[data_users[user_id]].settings["func_except"][id_chat]["del"]:
        inline_kb_list = [[IButton(text='🟢Отслеживание удалений сообщ.', callback_data=f'except_off_del_{id_chat}')]]
    else:
        inline_kb_list = [[IButton(text='🔴Отслеживание удалений сообщ.', callback_data=f'except_on_del_{id_chat}')]]
    if jarvis_all[data_users[user_id]].settings["func_except"][id_chat]["edit"]:
        inline_kb_list.append([IButton(text='🟢Отслеживание изменений сообщ.', callback_data=f'except_off_edit_{id_chat}')])
    else:
        inline_kb_list.append([IButton(text='🔴Отслеживание изменений сообщ.', callback_data=f'except_on_edit_{id_chat}')])
    if jarvis_all[data_users[user_id]].settings["func_except"][id_chat]["command"]:
        inline_kb_list.append([IButton(text='🟢Работа команд', callback_data=f'except_off_command_{id_chat}')])
    else:
        inline_kb_list.append([IButton(text='🔴Работа команд', callback_data=f'except_on_command_{id_chat}')])
    inline_kb_list.append([IButton(text='🗑️Удалить из особых настроек', callback_data=f'except_delete_{id_chat}')])
    inline_kb_list.append([IButton(text='«', callback_data='except_chats')])
    return IMarkup(inline_keyboard=inline_kb_list)