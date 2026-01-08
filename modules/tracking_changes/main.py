import asyncio, time
from functions.functions import My_message
from TelegramClient import Jarvis_client
from create_bot import bot
from telethon.tl import types
from config import jarvis_all, data_users
from modules.tracking_changes.settings import PATH
from telethon.errors import UsernameInvalidError

status = True

async def call_on_web(jarvis : Jarvis_client, chat_id):
    start_time = time.time()
    while time.time() - start_time < 60 * 60* 24:
        from_user = await jarvis.client.get_entity(chat_id)
        if chat_id not in jarvis.modules_data["online"]:
            return
        if isinstance(from_user.status, types.UserStatusOnline):
            jarvis.modules_data["online"].remove(chat_id)
            return await bot.send_message(jarvis.user.id, f"<a href='tg://user?id={from_user.id}'>{from_user.first_name}</a> зашёл в телеграмм!")
        await asyncio.sleep(5)

async def start(jarvis : Jarvis_client, new_message : My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]:
        return
    
    if not "online" in jarvis.modules_data:
        jarvis.modules_data["online"] = []
    message = new_message.message
    if message.chat_id < 0:
        return
    
    text = message.text.lower()
    text_split = text.split()
    if len(text_split) < 2:
        return
    if "переста" in text_split[0] and "ждать" in text_split[1] and ("в сети" in text or "появления" in text):
        jarvis.modules_data["online"].remove(from_user.id)
        return await jarvis.send_message(message, f"Хорошо! Теперь я не жду появления {user} в сети!")
    
    if not ("в сети" in text and ("уведоми" in text_split[0] or "скажи" in text_split[0] or "сообщи" in text_split[0] or "напиши" in text_split[0])):
        return
    
    if "@" in text:
        find = text.split("@")[1].split()[0]
    elif "tg://user?id=" in text:
        find = text.split("tg://user?id=")[1].split("\">")[0]
    else:
        find = message.chat_id
    try:
        from_user = await jarvis.client.get_entity(find)
    except UsernameInvalidError:
        return await jarvis.send_message(message, f"Пользователь с именем пользователя {find} не найден!")
    if from_user.id == jarvis.user.id:
        return
    try:
        if from_user.bot:
            return
    except:
        pass
    user = f"<a href='tg://user?id={from_user.id}'>{from_user.first_name}</a>"
    if message.chat_id in jarvis.modules_data["online"]:
        return await jarvis.send_message(message, f"Я уже ожидаю появления {user} в сети!")
    if isinstance(from_user.status, types.UserStatusEmpty) or isinstance(from_user.status, types.UserStatusRecently):
        return await jarvis.send_message(message, f"К можалению, невозможно отслеживать статус {user} из-за настроек конфиденциальности пользователя!")
    jarvis.modules_data["online"].append(from_user.id)
    asyncio.create_task(call_on_web(jarvis, from_user.id))
    return await jarvis.send_message(message, f"Хорошо! Я сообщу, как только {user} появится в сети!")
