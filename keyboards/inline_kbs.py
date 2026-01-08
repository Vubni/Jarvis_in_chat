from aiogram.types import WebAppInfo
from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import config
from config import jarvis_all, data_users
from aiogram.types import KeyboardButton as KButton
from aiogram.types import ReplyKeyboardMarkup as RMarkup
from aiogram.types import KeyboardButtonRequestUser as KUser
from aiogram.types import KeyboardButtonRequestChat as KChat
from functions.reg import check_admin

def main():
    inline_kb_list = [[IButton(text="ⓘПрофиль", callback_data="profile"), IButton(text="⚙Основные настройки", callback_data="main_settings")],
        [IButton(text="📋Список команд", url=config.ARTICLE_COMMAND_URL), IButton(text="🤝Реферальная программа", callback_data="referal")],
        [IButton(text="👁️Функционал в чатах", callback_data="monitored"), IButton(text="️🛡Джарвис админ", callback_data="only_business")],
        [IButton(text="🛠️Команды", callback_data="commands"), IButton(text="🧩Модули", callback_data="modules")],
        [IButton(text="💡Идеи и предложения", callback_data="test")],
        [IButton(text="📑Контакты", callback_data="contacts"), IButton(text="📊Статистика бота", callback_data="stats")]]
    return IMarkup(inline_keyboard=inline_kb_list)

def referal():
    inline_kb_list = [[IButton(text="💬Сообщение для друга", callback_data="referal_2")],
        [IButton(text="«", callback_data="page")]]
    return IMarkup(inline_keyboard=inline_kb_list)

async def profile(user_id):
    inline_kb_list = [[IButton(text="🌟Оформить подписку", web_app=WebAppInfo(url=config.SUBSCRIPTION_URL))],
        [IButton(text="🔐Использовать промокод", callback_data="use_promo_code")]]
    if await check_admin(user_id, 3):
        inline_kb_list.append([IButton(text="🛡️Панель Администратора", callback_data="admin_panel")])
    inline_kb_list.append([IButton(text="«", callback_data="page")])
    return IMarkup(inline_keyboard=inline_kb_list)

def commands():
    inline_kb_list = []
    temp = []
    for item in config.modules:
        name = config.modules[item]["settings"].NAME
        uniq_id = config.modules[item]["settings"].UNIQ_ID
        temp.append(IButton(text=name, callback_data=uniq_id))
        if len(temp) == 2:
            inline_kb_list.append(temp)
            temp = []
    if temp:
        inline_kb_list.append(temp)
    inline_kb_list.append([IButton(text="«", callback_data="page")])
    return IMarkup(inline_keyboard=inline_kb_list)

def modules():
    inline_kb_list = [[IButton(text="💬Автоответчик", callback_data="answering"), IButton(text="💬Быстрые ответы", callback_data="quick_answers")],
        [IButton(text="💡Умный дом", callback_data="smart_home"), IButton(text="🛡️Антиспам", callback_data="antispam")],
        [IButton(text="📣Сообщения внимания", callback_data="attention"), IButton(text="☁Облако", callback_data="test")],
        [IButton(text="🕵️‍♂️Анон. вопросы", callback_data="test"), IButton(text="Синхрон. с Яндекс", callback_data="test")]]
    inline_kb_list.append([IButton(text="«", callback_data="page")])
    return IMarkup(inline_keyboard=inline_kb_list)

def new():
    inline_kb_list = [[IButton(text="🔗Подключить бота", callback_data="connect_bot")],
    [IButton(text="📋Список команд", url=config.ARTICLE_COMMAND_URL), IButton(text="📊Статистика бота", callback_data="stats")],
    [IButton(text="📑Контакты", callback_data="contacts"), IButton(text="🌐Канал", url="https://t.me/jarvis_in_chat")]]
    return IMarkup(inline_keyboard=inline_kb_list)

def connect_off():
    inline_kb_list = [[IButton(text='🔗Подключить бота', web_app=WebAppInfo(url=config.CONNECT_BOT_URL))],
                [IButton(text="Написать причину отключения", callback_data="reason_off")]]
    return IMarkup(inline_keyboard=inline_kb_list)

def connect_again():
    inline_kb_list = [[IButton(text='🔗Подключить бота', web_app=WebAppInfo(url=config.CONNECT_BOT_URL))]]
    return IMarkup(inline_keyboard=inline_kb_list)

def main_settings(status, user_id):
    if not jarvis_all[data_users[user_id]].subscription:
        inline_kb_list = [[IButton(text="⚙️Изменить префикс", callback_data="pro+")],
                        [IButton(text="🟢Пересылать мне посты из канала", callback_data="pro+")]]
    else:
        inline_kb_list = [[IButton(text="⚙️Изменить префикс", callback_data="edit_prefix")]]
        if jarvis_all[data_users[user_id]].settings["advertisement"]:
            inline_kb_list.append([IButton(text="🟢Пересылать мне посты из канала", callback_data="advert_off")])
        else:
            inline_kb_list.append([IButton(text="🔴Пересылать мне посты из канала", callback_data="advert_on")])
    if status:
        inline_kb_list.append([IButton(text="🟢Джарвис активен", callback_data="off_bot")])
    else:
        inline_kb_list.append([IButton(text="🔴Джарвис неактивен", callback_data="on_bot")])
    inline_kb_list.append([IButton(text="«", callback_data="page")])
    return IMarkup(inline_keyboard=inline_kb_list)

def edit_prefix(user_id):
    inline_kb_list = []
    if jarvis_all[data_users[user_id]].settings["prefix"]["status"]:
        inline_kb_list.append([IButton(text="🟢Префикс активен", callback_data="prefix_off")])
        if jarvis_all[data_users[user_id]].settings["prefix"]["text"] != "Джарвис":
            inline_kb_list.append([IButton(text="♻️Восстановить 'Джарвис'", callback_data="prefix_jarvis")])
        inline_kb_list.append([IButton(text="🔧Изменить префикс", callback_data="prefix_edit")])
    else:
        inline_kb_list.append([IButton(text="🔴Префикс неактивен", callback_data="prefix_on")])
    inline_kb_list.append([IButton(text="«", callback_data="main_settings")])
    return IMarkup(inline_keyboard=inline_kb_list)


def pay_support():
    return IMarkup(inline_keyboard=[[IButton(text="Написать (Write)", url="https://t.me/vubni")]])

def contacts():
    inline_kb_list = [[IButton(text="📝Написать", url="https://t.me/Vubni")],
            [IButton(text="«", callback_data="page")]]
    return IMarkup(inline_keyboard=inline_kb_list)

def connect_bot():
    inline_kb_list = [[IButton(text="🔗Подключить бота", web_app=WebAppInfo(url=config.CONNECT_BOT_URL))],
            [IButton(text="«", callback_data="start")]]
    return IMarkup(inline_keyboard=inline_kb_list)

def promo():
    inline_kb_list = [[IButton(text="🔖Использовать промокод", callback_data="use_promo_code")],
            [IButton(text="Продолжить без промокода", callback_data="oplata")]]
    return IMarkup(inline_keyboard=inline_kb_list)

def del_msg(id_or_us):
    if type(id_or_us) == str:
        button = [IButton(text="Перейти в личную переписку", url=f"https://t.me/{id_or_us}")]
    else:
        button = [IButton(text="Перейти в личную переписку", url=f"tg://user?id={id_or_us}")]
    inline_kb_list = [button,
            [IButton(text="⚙️Настроить личные чаты", callback_data="monitored_chats")]]
    return IMarkup(inline_keyboard=inline_kb_list)

def del_msg_gr(id_or_us, msg_id):
    if type(id_or_us) == str:
        button = [IButton(text="Перейти в группу", url=f"https://t.me/{id_or_us}/{msg_id}")]
    else:
        button = [IButton(text="Перейти в группу", url=f"https://t.me/c/{id_or_us}/{msg_id}")]
    inline_kb_list = [button,
            [IButton(text="⚙️Настроить группы", callback_data="monitored_groups")]]
    return IMarkup(inline_keyboard=inline_kb_list)

def settings_currency(user_id):
    if jarvis_all[data_users[user_id]].settings["currency"]:
        inline_kb_list = [[IButton(text='🟢Срабатывать на сообщ. содержащее валюту.', callback_data=f'currency|off')]]
    else:
        inline_kb_list = [[IButton(text='🔴Срабатывать на сообщ. содержащее валюту.', callback_data=f'currency|on')]]
    inline_kb_list.append([IButton(text='«', callback_data=f'commands')])
    return IMarkup(inline_keyboard=inline_kb_list)

def settings_attention(user_id):
    if not jarvis_all[data_users[user_id]].settings["attention"]["status"]:
        inline_kb_list = [[IButton(text='🔴Не активен', callback_data=f'atten|all|on')]]
    else:
        inline_kb_list = [[IButton(text='🟢Активен', callback_data='atten|all|off')]]
        if jarvis_all[data_users[user_id]].settings["attention"]["news"]:
            inline_kb_list.append([IButton(text='🟢Сообщение новостей', callback_data='atten|news|off')])
        else:
            inline_kb_list.append([IButton(text='🔴Сообщение новостей', callback_data='atten|news|on')])
        inline_kb_list.append([IButton(text='⚙️Изменить новостной канал', callback_data='atten|edit|news')])
        if jarvis_all[data_users[user_id]].settings["attention"]["weather"]["status"]:
            inline_kb_list.append([IButton(text='🟢Сообщение погоды', callback_data='atten|weat|off')])
        else:
            inline_kb_list.append([IButton(text='🔴Сообщение погоды', callback_data='atten|weat|on')])
        inline_kb_list.append([IButton(text='⚙️Изменить город', callback_data='atten|edit|weat')])
        if jarvis_all[data_users[user_id]].settings["attention"]["currency"]:
            inline_kb_list.append([IButton(text='🟢Сообщение курса валют', callback_data='atten|curren|off')])
        else:
            inline_kb_list.append([IButton(text='🔴Сообщение курса валют', callback_data='atten|curren|on')])
    inline_kb_list.append([IButton(text='«', callback_data=f'modules')])
    return IMarkup(inline_keyboard=inline_kb_list)

def settings_smarthome():
    inline_kb_list = [[IButton(text='⛓️‍💥Отвязать Яндекс аккаунт', callback_data="smart|off")], 
                      [IButton(text='«', callback_data='modules')]]
    return IMarkup(inline_keyboard=inline_kb_list)

def create_smarthome():
    inline_kb_list = [[IButton(text='«', callback_data='modules')]]
    return IMarkup(inline_keyboard=inline_kb_list)

def quick_answers(answers, subscription):
    inline_kb_list = []
    row = []
    indx = 1
    for item in answers:
        row.append(IButton(text=item["phrase"], callback_data='quick|' + item["id"]))
        if indx % 2 == 0:
            inline_kb_list.append(row)
            row = []
        indx += 1
    if row:
        inline_kb_list.append(row)
    if len(answers) < config.LIMIT_QUICK_ANSWERS:
        inline_kb_list.append([IButton(text='Создать быстрый ответ', callback_data='create|quick')])
    elif subscription:
        inline_kb_list.append([IButton(text='Создать быстрый ответ', callback_data='create|quick')])
    inline_kb_list.append([IButton(text='«', callback_data='modules')])
    return IMarkup(inline_keyboard=inline_kb_list)

def quick_answer(id_answer):
    inline_kb_list = [[IButton(text='Удалить быстрый ответ', callback_data=f"quick|del|{id_answer}")], 
                      [IButton(text='«', callback_data='quick_answers')]]
    return IMarkup(inline_keyboard=inline_kb_list)

def browser_settings(user_id):
    if jarvis_all[data_users[user_id]].settings["browser"] == 0:
        inline_kb_list = [[IButton(text='🟢Google', callback_data=f'browser|-1')],
        [IButton(text='⭕Яндекс', callback_data=f'browser|1')],
        [IButton(text='⭕Bing', callback_data=f'browser|2')]]
    elif jarvis_all[data_users[user_id]].settings["browser"] == 1:
        inline_kb_list = [[IButton(text='⭕Google', callback_data=f'browser|0')],
        [IButton(text='🟢Яндекс', callback_data=f'browser|-1')],
        [IButton(text='⭕Bing', callback_data=f'browser|2')]]
    elif jarvis_all[data_users[user_id]].settings["browser"] == 2:
        inline_kb_list = [[IButton(text='⭕Google', callback_data=f'browser|0')],
        [IButton(text='⭕Яндекс', callback_data=f'browser|1')],
        [IButton(text='🟢Bing', callback_data=f'browser|-1')]]
    inline_kb_list.append([IButton(text='«', callback_data='commands')])
    return IMarkup(inline_keyboard=inline_kb_list)

def antispam_settings(user_id):
    subscription = jarvis_all[data_users[user_id]].subscription
    if not subscription:
        inline_kb_list = [[IButton(text='⚙️Чувствительность', callback_data='pro+')]]
    else:
        inline_kb_list = [[IButton(text='⚙️Чувствительность', callback_data='anti|sens')]]
    
    if jarvis_all[data_users[user_id]].settings["antispam"]["status_chats"]:
        inline_kb_list.append([IButton(text='🟢Личные чаты', callback_data='anti|off_ch')])
    else:
        inline_kb_list.append([IButton(text='🔴Личные чаты', callback_data='anti|on_ch')])
        
    if not subscription:
        inline_kb_list.append([IButton(text='🔴Группы', callback_data='pro+')])
    elif jarvis_all[data_users[user_id]].settings["antispam"]["status_groups"]:
        inline_kb_list.append([IButton(text='🟢Группы', callback_data='anti|off_gr')])
    else:
        inline_kb_list.append([IButton(text='🔴Группы', callback_data='anti|on_gr')])
        
    if not subscription:
        inline_kb_list.append([IButton(text='🔍Исключения', callback_data='pro+')])
    else:
        inline_kb_list.append([IButton(text='🔍Исключения', callback_data='anti|exc')])
    
    inline_kb_list.append([IButton(text='«', callback_data='modules')])
    return IMarkup(inline_keyboard=inline_kb_list)

async def antispam_except(user_id):
    inline_kb_list = []
    indx = 0
    for item in jarvis_all[data_users[user_id]].settings["antispam"]["except"]:
        name = await jarvis_all[data_users[user_id]].get_title_or_name(item)
        inline_kb_list.append([IButton(text=f'♻️Восстановить для {name}', callback_data=f'anti|exc|{indx}')])
        indx += 1
    inline_kb_list.append([IButton(text='«', callback_data='antispam')])
    return IMarkup(inline_keyboard=inline_kb_list)

def new_except_antispam(user_id):
    subscription = jarvis_all[data_users[user_id]].subscription
    keyboard = []
    number = 1
    if not subscription:
        number = config.LIMIT_CHATS_EXCEPT-len(jarvis_all[data_users[user_id]].settings["antispam"]["except"])
    if number > 0:
        keyboard = [[KButton(text="💭Настроить личный чат", request_user=KUser(request_id=0, user_is_bot=False))]]
        if subscription:
            keyboard.append([KButton(text="👥Настроить группу", request_chat=KChat(request_id=1, chat_is_channel=False))])
    return RMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)
    
def antispam_sensity(user_id):
    temp = ["🔴Щадящий", "🔴Рыцарь", "🔴Агрессивный"]
    sens = jarvis_all[data_users[user_id]].settings["antispam"]["sensitivity"]
    inline_kb_list = []
    for i in range(len(temp)):
        if sens-1 == i:
            inline_kb_list.append([IButton(text="🟢" + temp[i][1:], callback_data=f'anti|sens|{i}')])
            continue
        inline_kb_list.append([IButton(text=temp[i], callback_data=f'anti|sens|{i}')])
    inline_kb_list.append([IButton(text='«', callback_data='antispam')])
    return IMarkup(inline_keyboard=inline_kb_list)

def pin_message():
    inline_kb_list = [[IButton(text='🗑️Имитация удаления сообщения', callback_data='imitation_1')],
    [IButton(text='✏️Имитация изменения сообщения', callback_data='imitation_2')],
    [IButton(text='📜Список команд', url=config.ARTICLE_COMMAND_URL)],
    [IButton(text='🛠️Основное меню настроек', callback_data='start_no_delete')]]
    return IMarkup(inline_keyboard=inline_kb_list)

def create_answer():
    inline_kb_list = [[IButton(text='Ответ на первое сообщение', callback_data='create_answer_2')],
    [IButton(text='Обычный ответ', callback_data='create_answer_1')],
    [IButton(text='«', callback_data='answering')]]
    return IMarkup(inline_keyboard=inline_kb_list)

def create_answer_type_2():
    inline_kb_list = [[IButton(text='Обычный ответ', callback_data='answer_type_1')],
    [IButton(text='Ответ от Jarvis Ai', callback_data='test')],
    [IButton(text='«', callback_data='answering')]]
    return IMarkup(inline_keyboard=inline_kb_list)

def create_answer_type_all():
    inline_kb_list = [[IButton(text='Обычный ответ', callback_data='answer_type_1')],
    [IButton(text='Ответ, если не в сети', callback_data='answer_type_2')],
    [IButton(text='Ответ, если в сети', callback_data='answer_type_3')],
    [IButton(text='Ответ от Jarvis Ai', callback_data='test')],
    [IButton(text='«', callback_data='answering')]]
    return IMarkup(inline_keyboard=inline_kb_list)

def answer_settings(id_answer):
    inline_kb_list = [[IButton('🗑️Удалить', callback_data=f'answ_del_{id_answer}')],
    [IButton('«', callback_data='answering')]]
    return IMarkup(inline_keyboard=inline_kb_list)


def back(page="page"):
    return IMarkup(inline_keyboard=[[IButton(text="«", callback_data=page)]])