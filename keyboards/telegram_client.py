from aiogram.types import WebAppInfo
from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import config
from config import jarvis_all, data_users

def attention():
    inline_kb_list = [[IButton(text="Настройки оповещений", callback_data="attention_save_post")]]
    return IMarkup(inline_keyboard=inline_kb_list)

def off_connect():
    inline_kb_list = [[IButton(text="🔗Подключить повторно", web_app=WebAppInfo(url='https://business.jarvis-chat.vubni.com/auth/index.html'))], 
                       [IButton(text="Указать причину отключения", callback_data="reason_off")]]
    return IMarkup(inline_keyboard=inline_kb_list)

def ad_pro(chat_id):
    inline_kb_list = [[IButton(text="Перейти в группу", url=f"https://t.me/c/{chat_id}")], 
                       [IButton(text="🌟Оформить подписку", web_app=WebAppInfo(url=config.SUBSCRIPTION_URL))]]
    return IMarkup(inline_keyboard=inline_kb_list)

def subscription():
    inline_kb_list = [[IButton(text="🌟Оформить подписку", web_app=WebAppInfo(url=config.SUBSCRIPTION_URL))]]
    return IMarkup(inline_keyboard=inline_kb_list)