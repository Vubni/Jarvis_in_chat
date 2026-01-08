import wikipedia
from datetime import datetime
from functions.functions import My_message
from TelegramClient import Jarvis_client
from database.database import Database
from config import jarvis_all, data_users
from modules.wikipedia.settings import PATH

status = True

def search_wikipedia_article(query):
    try:
        search_results = wikipedia.search(query)
        if not search_results:
            return False, False, False
        closest_title = search_results[0]
        page = wikipedia.page(closest_title)
        return page.title, page.content[:300] + "...", page.url

    except wikipedia.exceptions.DisambiguationError as e:
        return False, False, False
    except wikipedia.exceptions.PageError:
        return False, False, False
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return False, False, False

async def start(jarvis : Jarvis_client, new_message : My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]:
        return
    
    message = new_message.message
    text = message.text.lower()
    if len(text.split()) > 1 and text.split()[0] == "википедия":
        text = text.replace("википедия", "")
        res, result, url = search_wikipedia_article(text)
        if not res:
            return await jarvis.send_message(message, f"К сожалению я не смог найти такую статью в википедии.")
        async with Database() as db:
            id = await db.fetchval("INSERT INTO open_web (url, date) VALUES ($1, $2)", (url, datetime.now().date()))
        return await jarvis.send_message(message, f"Я нашёл следующую статью в википедии.\n\nЗаголовок: {res}\n\nСодержание: {result}\n\n"
                                  f"Открыть полную статью можно по <a href='https://t.me/vubni_jarvis_bot/url?startapp={id}'>ссылке</a>!")
    