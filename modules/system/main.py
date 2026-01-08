from functions.functions import My_message
from TelegramClient import Jarvis_client
from telethon.tl import types, functions
from datetime import datetime, timedelta
import pytz, re
from config import jarvis_all, data_users
from modules.system.settings import PATH

status = True

def get_first_number_from_string(input_string):
    # Используем регулярное выражение для поиска числа
    match = re.search(r'\d+', input_string)  # \d+ ищет одну или несколько цифр подряд
    if match:
        return int(match.group())  # Возвращаем найденное число, преобразуя его в целое
    else:
        return None

async def start(jarvis : Jarvis_client, new_message : My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]:
        return
    
    message = new_message.message
    text = message.text.lower()
    chat = new_message.chat
    if not message.out:
        return
    if "в чс" == text or "заблокировать" == text:
        if isinstance(chat, types.User):
            await jarvis.client(functions.contacts.BlockRequest(chat.id))
            return await jarvis.send_message(message, f"<b>Контакт успешно заблокирован и добавлен в чс!</b>")
    if len(text.split()) < 7 and ("выключи уведомления" in text or "выключить уведомления" in text or "выключи звук" in text or "выключить звук" in text):
        result = await jarvis.client(functions.account.GetNotifySettingsRequest(chat))
        if not result.mute_until or result.mute_until < datetime.now(pytz.timezone('UTC')):
            number = get_first_number_from_string(text)
            if len(text.split()) == 2:
                await jarvis.client(functions.account.UpdateNotifySettingsRequest(chat, types.InputPeerNotifySettings(mute_until=timedelta(days=90))))
            else:
                if "лет" in text or 'год' in text:
                    await jarvis.client(functions.account.UpdateNotifySettingsRequest(chat, types.InputPeerNotifySettings(mute_until=timedelta(days=12*30*number))))
                elif "месяц" in text:
                    await jarvis.client(functions.account.UpdateNotifySettingsRequest(chat, types.InputPeerNotifySettings(mute_until=timedelta(days=30*number))))
                elif "день" in text or 'дни' in text:
                    await jarvis.client(functions.account.UpdateNotifySettingsRequest(chat, types.InputPeerNotifySettings(mute_until=timedelta(days=number))))
                elif "час" in text:
                    await jarvis.client(functions.account.UpdateNotifySettingsRequest(chat, types.InputPeerNotifySettings(mute_until=timedelta(hours=number))))
                elif "минут" in text:
                    await jarvis.client(functions.account.UpdateNotifySettingsRequest(chat, types.InputPeerNotifySettings(mute_until=timedelta(minutes=number))))
                elif "секунд" in text:
                    await jarvis.client(functions.account.UpdateNotifySettingsRequest(chat, types.InputPeerNotifySettings(mute_until=timedelta(seconds=number))))
                else:
                    return False
            return await jarvis.send_message(message, "<b>Уведомления успешно выключены!</b>")
        else:
            return await jarvis.send_message(message, "<b>Уведомления уже выключены!</b>")
    if "включи уведомления" == text or "включить уведомления" == text or "включи звук" == text or "включить звук" == text:
        result = await jarvis.client(functions.account.GetNotifySettingsRequest(chat))
        if not result.mute_until or result.mute_until < datetime.now(pytz.timezone('UTC')):
            return await jarvis.send_message(message, "<b>Уведомления уже включены!</b>")
        else:
            await jarvis.client(functions.account.UpdateNotifySettingsRequest(chat, types.InputPeerNotifySettings()))
            return await jarvis.send_message(message, "<b>Уведомления успешно включены!</b>")