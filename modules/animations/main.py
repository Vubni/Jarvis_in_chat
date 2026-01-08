from functions.functions import My_message
from TelegramClient import Jarvis_client
from telethon.tl.patched import Message
import asyncio
from core import cache_with_expiration
from config import jarvis_all, data_users
from modules.animations.settings import PATH

status = True
status_start = {}

async def start(jarvis : Jarvis_client, new_message : My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]["status"]:
        return
    
    message = new_message.message
    text = message.text.lower()
    user_id = new_message.from_user.id
    if message.out:
        if text == "❤️" and jarvis_all[data_users[user_id]].settings["modules"][PATH]["heart"]:
            if jarvis.user.id in status_start:
                status_start[jarvis.user.id].cancel()
            status_start[jarvis.user.id] = asyncio.create_task(animate_message(message, jarvis.user.id))
            return True
        elif text == '🪄' and jarvis_all[data_users[user_id]].settings["modules"][PATH]["magic"]: # волшебная палочка
            if jarvis.user.id in status_start:
                status_start[jarvis.user.id].cancel()
            status_start[jarvis.user.id] = asyncio.create_task(magic_anim(message, jarvis.user.id))
            return True

async def animate_message(message: Message, user_id):
    HEARTS = ['💖', '💝', '💘', '💗', '💓', '❣️', '❤️‍🔥', '🩷', '🧡', '💛', '💚', '💙', '💜', '🤍']
    for heart in HEARTS:
        await message.edit(heart)  # Изменяем текст сообщения
        await asyncio.sleep(0.5)
    await message.edit('❤️')  # Изменяем текст сообщения
    del status_start[user_id]

async def magic_anim(message: Message, user_id):
    magic_emojis = ['✨','🔥','💫','💥','⚡','🌈']
    # Цикл смены эмодзи
    for emoji in magic_emojis:
        await message.edit(emoji) # Редактируем сообщение
        await asyncio.sleep(1.5)  # Задержка 1.5 секунды
    await message.edit('🔮')  # Изменяем текст сообщения
    del status_start[user_id]