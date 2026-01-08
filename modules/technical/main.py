from functions.functions import My_message
from TelegramClient import Jarvis_client
import time, psutil
from telethon.tl import functions, types

status = True

async def start(jarvis : Jarvis_client, new_message : My_message):
    message = new_message.message
    text = message.text.lower()
    if text == "пинг":
        time_jarvis = time.perf_counter() - new_message.start_time
        start_time1 = time.perf_counter()
        await jarvis.client(functions.help.GetNearestDcRequest())
        percent = psutil.cpu_percent()
        if int(percent) == 0:
            percent = psutil.cpu_percent()
        text_answer = f"""ПОНГ!

Информация о подключении и скорости:
Скорость ответа Telegram: {((time.perf_counter() - start_time1) * 1000):.2f} мс
Скорость ответа Джарвис: {round((time_jarvis) * 1000, 2)} мс
Нагрузка на Джарвис: {percent}%"""
        return await jarvis.send_message(message, text_answer)
    elif "джарвис" in text and "ты тут" in text:
        return await jarvis.send_message(message, "<b>Ожидаю команды!</b>")
    