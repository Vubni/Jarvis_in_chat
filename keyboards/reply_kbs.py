from aiogram.types import KeyboardButton as KButton
from aiogram.types import ReplyKeyboardMarkup as RMarkup
from aiogram.types import KeyboardButtonRequestChat as RChat
from aiogram.types import WebAppInfo
import config

def attention_edit_news():
    kb_list = [
        [KButton(text="🌐Отправить канал", request_chat=RChat(request_id=0, chat_is_channel=True))],
        [KButton(text="❌Отмена")]
    ]
    keyboard = RMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)
    return keyboard

def yandex_connect():
    kb_list = [[KButton(text='🔗Привязать Яндекс аккаунт', web_app=WebAppInfo(url=config.CONNECT_SMARTHOME_URL))]]
    keyboard = RMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)
    return keyboard