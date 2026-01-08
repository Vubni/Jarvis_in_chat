from functions.functions import My_message
from TelegramClient import Jarvis_client
from telethon.tl.patched import Message
from config import jarvis_all, data_users
from modules.weather.settings import PATH
import re
import googlesearch as gs
from database.database import Database
from datetime import datetime

status = True
status_start = {}

def get_weather(text):
    try:
        text = "https://yandex.ru/search/?text=Какая погода в " + text + " Яндекс"
        results=gs.search(text,num_results=1)
        for link in results:
            return link
    except:
        return None

async def start(jarvis: Jarvis_client, new_message: My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]:
        return

    message = new_message.message
    text = message.text.lower()
    if ("погода в" in text or "какая сейчас погода" in text or "какая погода в" in text) and len(text.split(" ")) < 7:
        text = re.sub(r'[^a-zA-Zа-яА-Я0-9]', '', text.replace("какая сейчас погода в ", "").replace("какая погода в ", "").replace("погода в ", ""))
        url = get_weather(text)
        if not url:
            return 
        async with Database() as db:
            id = await db.fetchval("INSERT INTO open_web (url, date) VALUES ($1, $2)", (url, datetime.now().date()))
        await jarvis.send_message(message, f"Подробную информацию по погоде можно посмотреть по <a href=https://t.me/vubni_jarvis_bot/url?startapp={id}>ссылке</a>")