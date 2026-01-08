from core import *
import config
from functions.smart_home import Smart_home, Lamp_control
from config import jarvis_all, data_users
from json import dumps

from aiogram.types import (
    InlineQuery,
    InlineQueryResultPhoto,
    InlineQueryResultVideo,
    InlineQueryResultVoice,
    InputTextMessageContent,
    InlineQueryResultArticle,
    InlineQueryResultDocument,
    InlineQueryResultsButton,
    WebAppInfo
)

from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton
from aiogram import Router, F
from database.database import Database
import s3


@cache_with_expiration(20)
async def get_ad(user_id) -> list:
    async with Database() as db:
        result = await db.execute("SELECT * FROM advertisement WHERE balance > 0 ORDER BY RANDOM() LIMIT 1")
        await db.execute_all("UPDATE advertisement SET balance = balance - 0.30, count = count + 1 WHERE id = $1", (result["id"],))
    return result

async def get_saved_messages(user_id: int, query: str) -> list:
    async with Database() as db:
        saved_messages = await db.execute_all("SELECT * FROM saved_messages WHERE user_id=$1 AND name LIKE $2", (user_id, f"%{query}%"))
    return saved_messages


router_inline = Router()

async def management_smart_home(user_id: int, params: list[str]) -> InlineQueryResultArticle:
    try:
        smart_home_token = jarvis_all[data_users[user_id]].yandex_token
        smart_home = Smart_home(smart_home_token)
        devices = smart_home.get_devices()
    except:
        return False

    markup = IMarkup(inline_keyboard=[[IButton(text=devices[i]["name"], callback_data=f'sh|{i}')] for i in range(len(devices))])
    if len(params) == 1:  # @bot дом
        return InlineQueryResultArticle(
            id="99", title="Управление вашим умным домом", reply_markup=markup, input_message_content=InputTextMessageContent(
                message_text="Управление вашим умным домом. Выберите устройство ниже"))
    try:
        device_id = int(params[1])  # @bot дом <device_id>
        device = devices[device_id]
    except:  # Неверный device_id
        return InlineQueryResultArticle(
            id="99", title="Управление вашим умным домом", reply_markup=markup, input_message_content=InputTextMessageContent(
                message_text="Управление вашим умным домом. Выберите устройство ниже"))
    if "devices.types.light" in device["type"]:  # Если есть подключенная лампа
        lamp = Lamp_control(jarvis_all[data_users[user_id]].yandex_token, devices[device_id]["id"])
        buttons = [[IButton(text="🔴Выключить", callback_data=f"sh|{device_id}|off"),
                    IButton(text="🟢Включить", callback_data=f"sh|{device_id}|on")],
                   [IButton(text="Установить яркость", callback_data=f"sh|{device_id}|brig|0")],
                   [IButton(text="1%", callback_data=f"sh|{device_id}|brig|1"),
                    IButton(text="50%", callback_data=f"sh|{device_id}|brig|2"),
                    IButton(text="100%", callback_data=f"sh|{device_id}|brig|3")],
                   [IButton(text="-25%", callback_data=f"sh|{device_id}|brig|4"),
                    IButton(text="-10%", callback_data=f"sh|{device_id}|brig|5"),
                    IButton(text=lamp.brightness, callback_data=f"sh|{device_id}|brig|0"),
                    IButton(text="+10%", callback_data=f"sh|{device_id}|brig|6"),
                    IButton(text="+25%", callback_data=f"sh|{device_id}|brig|7")]]
        if lamp.color:
            buttons.append([[IButton(text="Выбрать цвет", callback_data="sh|color|0")],
                            [IButton(text="⚪️☀️", callback_data=f"sh|{device_id}|color|1"),
                             IButton(text="⚪️❄️", callback_data=f"sh|{device_id}|color|2"),
                             IButton(text="🔴", callback_data=f"sh|{device_id}|color|3"),
                             IButton(text="🔵", callback_data=f"sh|{device_id}|color|4"),
                             IButton(text="🟣", callback_data=f"sh|{device_id}|color|5")],
                            [IButton(text="🟢", callback_data=f"sh|{device_id}|color|6"),
                             IButton(text="🟤", callback_data=f"sh|{device_id}|color|7"),
                             IButton(text="🟠", callback_data=f"sh|{device_id}|color|8"),
                             IButton(text="🟡", callback_data=f"sh|{device_id}|color|9")]])
        if lamp.color_scene:
            buttons.append([IButton(text="Выберите сценарий", callback_data="sh|scene|0")])
            buttons_temp = []
            for i in range(len(lamp.color_scene)):
                if len(buttons_temp) == 3:
                    buttons.append(buttons_temp)
                    buttons_temp.clear()
                buttons_temp.append(IButton(text=str(lamp.color_scene[i]), callback_data=f"sh|{device_id}|scene|{i+1}"))
            if buttons_temp:
                buttons.append(buttons_temp)
        buttons.append([IButton(text="Назад", callback_data="sh|")])
        return InlineQueryResultArticle(
            id="99", title="Управление вашим умным домом", input_message_content=InputTextMessageContent(
                message_text=f"Возможности для устройства '{devices[device_id]['name']}'"),
            reply_markup=IMarkup(inline_keyboard=buttons))
    else:  # Нет подключенной лампы
        return InlineQueryResultArticle(
            id="99", title="Управление вашим умным домом", reply_markup=markup, input_message_content=InputTextMessageContent(
                message_text="Управление вашим умным домом. Выберите устройство ниже"))


@router_inline.inline_query()
async def inline_handler(inline_query: InlineQuery):
    user_id = inline_query.from_user.id
    results = []
    
    if not jarvis_all.get(data_users.get(user_id)):  # Если неподключенный пользователь
        await inline_query.answer(results, cache_time=0, is_personal=True, button=InlineQueryResultsButton(text="🔗Подключить бота", web_app=WebAppInfo(url=config.CONNECT_BOT_URL)))
        return
    
    if not jarvis_all[data_users[user_id]].subscription:
        ad = await get_ad(inline_query.from_user.id)
        if ad:  # Показ рекламы
            content_ad = ad["content"]
            name_button_ad = ad["name_button"]
            url_ad = ad["url"]
            markup = IMarkup(inline_keyboard=[[IButton(text=name_button_ad, url=url_ad)]])
            results.append(InlineQueryResultArticle(
                id="0", title=f"Реклама: {content_ad}", reply_markup=markup, input_message_content=InputTextMessageContent(
                    message_text=f"{content_ad}\n[{name_button_ad}]({url_ad})")))
            
    params = inline_query.query.split()
    if jarvis_all[data_users[user_id]].yandex_token:  # Показ меню умного дома
        temp = await management_smart_home(user_id, params)
        if temp:
            results.append(temp)
    saved_messages = await get_saved_messages(inline_query.from_user.id, inline_query.query)
    for index, saved_message in enumerate(saved_messages):  # Показ всех сохраненных сообщений
        i = str(index+1)
        markup = IMarkup(inline_keyboard=[[IButton(text="Удалить из облака", callback_data="cloud|" + str(saved_message["id"]))]])
        text = str(saved_message["text"])
        name = str(saved_message["name"])
        if saved_message["content"]:
            try:
                media_token = saved_message["content"].split("=")[1]
                url = await s3.generate_presigned_url(f"cloud/{media_token}")
                if not url:
                    continue
            except:
                continue
            if "photo=" in saved_message["content"]:
                results.append(InlineQueryResultPhoto(
                    id=i, photo_url=url, title=name,
                    thumbnail_url=url, description=text,
                    caption=text, reply_markup=markup))
            elif "video=" in saved_message["content"]:
                results.append(InlineQueryResultVideo(
                    id=i, video_url=url, mime_type="video/mp4",
                    thumbnail_url=config.URL + "images/logo.png", title=name, description=text,
                    caption=text, reply_markup=markup))
            elif "voice=" in saved_message["content"]:
                results.append(InlineQueryResultVoice(
                    id=i, voice_url=url, title=name, description=text, caption=text, reply_markup=markup))
            elif "document=" in saved_message["content"]:
                file = await s3.get_metadata(f"cloud/{media_token}")
                results.append(InlineQueryResultDocument(
                    id=i, title=name, document_url=url, mime_type=file["Content-Type"],
                    description=text, caption=text, reply_markup=markup))
        else:
            results.append(InlineQueryResultArticle(
                id=i, title=name, reply_markup=markup, description=text, input_message_content=
                InputTextMessageContent(message_text=text)))
    await inline_query.answer(results, cache_time=0, is_personal=True)
