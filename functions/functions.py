from bs4 import BeautifulSoup
import bs4
import string, random, requests
from core import cache_with_expiration
import googlesearch as gs
import os
import importlib.util

import config, time, asyncio
from create_bot import bot

from telethon.tl.patched import Message
import telethon.tl.types as tl_types
from telethon.events.newmessage import NewMessage
from typing import Union

from database.database import Database
from datetime import datetime, timedelta

class My_message():
    def __init__(self, event : NewMessage.Event, message : Message, from_user : Union[tl_types.User, tl_types.Channel, tl_types.Chat]) -> None:
        self.event = event
        self.message = message
        self.chat = event.chat if event.chat else event.chat_id
        self.from_user = from_user
        self.start_time = time.perf_counter()

    async def reply_message_init(self):
        self.reply_message = await self.message.get_reply_message()
    


@cache_with_expiration(15)
async def get_ad(user_id, count=1) -> list:
    try:
        if (await bot.get_chat_member(-1002237639994, user_id)).status == 'left':
            return "Поддержите функционал бесплатного бота подпиской на <a href='https://t.me/jarvis_in_chat'>канал</a>, после чего эта надпись пропадёт."
    except:
        return "Поддержите функционал бесплатного бота подпиской на <a href='https://t.me/jarvis_in_chat'>канал</a>, после чего эта надпись пропадёт."
    
    async with Database() as db:
        result = await db.execute("SELECT * FROM advertisement WHERE balance > 0 ORDER BY RANDOM() LIMIT 1")
        await db.execute("UPDATE advertisement SET balance=balance-(0.30*$1), count=count+$1 WHERE id=$2", (count, result["id"]))
    content = result["content"]
    button_name = result["name_button"]
    url = result["url"]
    return f"<i>{content}\n<a href='{url}'>{button_name}</a></i>"

async def create_promo(type : str, bonus: int, date_length : int) -> str:
    date = (datetime.now() + timedelta(date_length)).date()
    code = generate_random_name(5)
    async with Database() as db:
        await db.execute("INSERT INTO promo_codes (code, type, bonus, limit_day) VALUES ($1, $2, $3)", (code, type, bonus, date))
    return code

def pluralize(count, forms):
    if count % 10 == 1 and count % 100 != 11:
        return forms[0]
    elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        return forms[1]
    else:
        return forms[2]

def convert_seconds(seconds):
    units = [
        (('день', 'дня', 'дней'), 86400),
        (('час', 'часа', 'часов'), 3600),
        (('минута', 'минуты', 'минут'), 60),
        (('секунда', 'секунды', 'секунд'), 1)
    ]
    
    for i in range(len(units)):
        unit_forms, unit_value = units[i]
        if seconds >= unit_value:
            count = seconds // unit_value
            remainder = seconds % unit_value
            unit_str = pluralize(count, unit_forms)
            
            if i + 1 < len(units):
                next_forms, next_value = units[i+1]
                next_count = round(remainder / next_value)
                next_str = pluralize(next_count, next_forms)
                return f"{count} {unit_str}, {next_count} {next_str}"
            else:
                return f"{count} {unit_str}, 0 секунд"
    
    return "0 секунд"


def import_modules():
    print("-----------------------------")
    print("Инициализированы модули:")
    modules = {}
    for folder_name in os.listdir(config.MODULES_PATH):
        folder_path = os.path.join(config.MODULES_PATH, folder_name)
        if os.path.isdir(folder_path):
            main_path = os.path.join(folder_path, 'main.py')
            settings_path = os.path.join(folder_path, 'settings.py')
            if os.path.exists(main_path) and os.path.exists(settings_path):
                try:
                    # Загрузка main.py
                    main_spec = importlib.util.spec_from_file_location(f"{folder_name}.main", main_path)
                    main_module = importlib.util.module_from_spec(main_spec)
                    main_spec.loader.exec_module(main_module)
                except Exception as e:
                    print("error init module ", folder_name, " for main.py. Info: ", e)
                
                try:
                    # Загрузка settings.py
                    settings_spec = importlib.util.spec_from_file_location(f"{folder_name}.settings", settings_path)
                    settings_module = importlib.util.module_from_spec(settings_spec)
                    settings_spec.loader.exec_module(settings_module)
                except Exception as e:
                    print("error init module ", folder_name, " for settings.py. Info: ", e)
                
                # Проверка статуса
                if (hasattr(main_module, 'status') and main_module.status):
                    modules[folder_name] = {
                        'main': main_module,
                        'settings': settings_module
                    }
                    print(folder_name)
    print("-----------------------------\n")
    return modules


class LimitedSizeList:
    def __init__(self, max_size):
        self.max_size = max_size
        self.data = []

    def append(self, item):
        if len(self.data) >= self.max_size:
            self.data.pop(0)  # Удаление старейшего элемента
        self.data.append(item)

    def __repr__(self):
        return repr(self.data)

    def to_list(self):
        return self.data

def clean_html(html_content):
    try:
        # Поддерживаемые теги в Telegram API
        supported_tags = {
            'b', 'i', 'u', 's', 'code', 'pre', 'a', 'blockquote',
            'tg:break', 'tg:image', 'tg:video'  # и другие, если нужно
        }

        try:
            # Создаем объект BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
        except bs4.MarkupResemblesLocatorWarning:
            return html_content

        # Проходим по всем тегам в содержимом
        for tag in soup.find_all(True):  # True находит все теги
            if tag.name not in supported_tags:
                tag.unwrap()  # Удаляем тег

        return str(soup)
    except:
        return html_content

def generate_random_name(number : int = 16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(number))

@cache_with_expiration(6 * 60 * 60)
def get_crypto_price(crypto_id, vs_currency="usd"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies={vs_currency}&include_24hr_change=true"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return float(data[crypto_id][vs_currency]), float(data[crypto_id]["usd_24h_change"])
    else:
        return None
    
def get_weather(text):
    try:
        text = "https://yandex.ru/search/?text=Какая погода в " + text + " Яндекс"
        results=gs.search(text,num=1,stop=1,pause=0)
        for link in results:
            return link
    except:
        return None