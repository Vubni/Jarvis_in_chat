from functions.functions import My_message
from TelegramClient import Jarvis_client
from telethon.tl import types, functions
from datetime import datetime, timedelta
import pytz, re
from config import jarvis_all, data_users
from modules.smart_home.settings import PATH

status = True

async def start(jarvis : Jarvis_client, new_message : My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]:
        return
    
    text = new_message.message.text.lower()
    if "умный дом" == text:
        message = new_message.message
        inline_query = (await jarvis.client.inline_query("@vubni_jarvis_bot", query="smart_home", entity=message.chat_id)).result
        await jarvis.client(functions.messages.SendInlineBotResultRequest(
            peer=message.chat_id,
            query_id=inline_query.query_id,
            id=inline_query.results[0].id,
            hide_via=True
        ))