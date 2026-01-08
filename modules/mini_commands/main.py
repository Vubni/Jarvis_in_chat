from functions.functions import My_message
from TelegramClient import Jarvis_client
import random, re
from database.database import Database
from datetime import datetime
from config import jarvis_all, data_users
from modules.mini_commands.settings import PATH

status = True

def get_random_number(range_str):
    parts = range_str.split()
    start = 0
    try:
        if len(parts) == 1:
            end = int(parts[0])
        elif len(parts) == 2:
            start = int(parts[0])
            end = int(parts[1])
        else:
            start = 0
            end = 10
    except:
        return "Некорректный формат команды"
    random_number = random.randint(min(start, end), max(start, end))
    return "И выпадает число... <b>" + str(random_number) + "</b>!"

async def start(jarvis : Jarvis_client, new_message : My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]:
        return
    message = new_message.message
    text = message.text.lower()
    text_splited = text.split()
    
    if "рандом" == text_splited[0] and len(text_splited) <= 3:
        return await jarvis.send_message(message, get_random_number(text.replace("рандом", "")))
    if "данет" == text_splited[0]:
        return await jarvis.send_message(message, "Я думаю, что <b>" + random.choice(["Да", "Нет"]) + "</b>")
    if ("все сообщения" == text or ("сколько" in text and "сообщений" in text)) and len(text_splited) <= 5:
        messages_count = (await jarvis.client.get_messages(new_message.chat, limit=0)).total
        return await jarvis.send_message(message, f"В этом чате я насчитал {messages_count} сообщений!")
    if ("браузер" in text and ("яндекс" in text or "yandex" in text)) and len(text_splited) <= 2:
        async with Database() as db:
            id = await db.fetchval("INSERT INTO open_web (url, date) VALUES ($1, $2)", ("https://ya.ru", datetime.now().date()))
        return await jarvis.send_message(message, f"Я помогу! [Открыть браузер](https://t.me/vubni_jarvis_bot/url?startapp={id})")
    if ("браузер" in text and ("гугл" in text or "google" in text)) and len(text_splited) <= 2:
        async with Database() as db:
            id = await db.fetchval("INSERT INTO open_web (url, date) VALUES ($1, $2)", ("https://google.com", datetime.now().date()))
        return await jarvis.send_message(message, f"Я помогу! [Открыть браузер](https://t.me/vubni_jarvis_bot/url?startapp={id})")
    if ("браузер" in text and ("бинг" in text or "bing" in text)) and len(text_splited) <= 2:
        async with Database() as db:
            id = await db.fetchval("INSERT INTO open_web (url, date) VALUES ($1, $2)", ("https://www.bing.com", datetime.now().date()))
        return await jarvis.send_message(message, f"Я помогу! [Открыть браузер](https://t.me/vubni_jarvis_bot/url?startapp={id})")
    if "браузер" == text:
        temp = ["https://google.com", "https://ya.ru", "https://www.bing.com"]
        async with Database() as db:
            id = await db.fetchval("INSERT INTO open_web (url, date) VALUES ($1, $2)", (temp[jarvis.settings["browser"]], datetime.now().date()))
        return await jarvis.send_message(message, f"Я помогу! [Открыть браузер](https://t.me/vubni_jarvis_bot/url?startapp={id})")
    if ("отмена" == text or 'не' == text or 'не надо' == text or "нет" == text or "нахуй" == text or "стоп" == text or "выключись" == text or "выключить" == text) and len(text_splited) == 1:
        if message.chat_id in jarvis.jarvis_ai:
            jarvis.jarvis_ai.remove(message.chat_id)
            return await jarvis.send_message(message, "Я продолжу ждать команды, но всегда готов с вами поболтать!")
    elif text == "джарвис!":
        return await jarvis.send_message(message, f"<b>Функция временно отключена.</b>\n<a href='https://t.me/jarvis_in_chat/130'>Подробнее</a>")