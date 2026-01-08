from functions.functions import My_message
from TelegramClient import Jarvis_client
from database.database import Database
from telethon.tl import types
from functions.functions import clean_html
from config import jarvis_all, data_users
from modules.info_user.settings import PATH
import re

status = True

async def start(jarvis : Jarvis_client, new_message : My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]:
        return

    message = new_message.message
    text = message.text.lower()
    if len(text.split()) in [3, 4] and "информация о " in text:
        entity = None
        if "@" in text:
            username = re.search(r'@(\w+)', text)
            if username:
                try:
                    entity = await jarvis.client.get_entity(username.group(1))
                except (ValueError, TypeError):
                    pass
        elif "tg://user?id=" in text:
            user_id = re.search(r'tg://user\?id=(\d+)', text)
            if user_id:
                try:
                    entity = await jarvis.client.get_entity(int(user_id.group(1)))
                except (ValueError, TypeError):
                    pass
        else:
            user_id = re.search(r'(\d+)', text)
            if user_id:
                try:
                    entity = await jarvis.client.get_entity(int(user_id.group(1)))
                except (ValueError, TypeError):
                    pass

        if not entity:
            return

        if isinstance(entity, types.User):
            await handle_user_info(jarvis, message, entity)
        elif isinstance(entity, (types.Chat, types.Channel)):
            await handle_group_info(jarvis, message, entity)
        else:
            await jarvis.send_message(message, "Не удалось определить сущность")

async def handle_user_info(jarvis, message, user):
    countries = ["США", "Европа", "Австралия", "Азия", "Южная Азия"]
    dc_info = f"Датацентр: {user.photo.dc_id} ({countries[user.photo.dc_id-1]})" if user.photo else "Датацентр неизвестен"
    
    status = "онлайн" if isinstance(user.status, types.UserStatusOnline) else "офлайн"
    phone = f"Телефон: {user.phone}" if user.phone else "Телефон: не найден"
    bot_status = "Да" if user.bot else "Нет"
    lang = f"Язык: {user.lang_code}" if user.lang_code else "Язык: не определён"
    
    async with Database() as db:
        jarvis_connected = "Да" if await db.execute("SELECT id FROM profiles WHERE user_id=$1", (user.id,)) else "Нет"
        complaints = await db.execute("SELECT COUNT(*) FROM complaints WHERE user_id=$1", (user.id,))
        rating = 100 - int(complaints.get('count', 0)) if complaints else 100

    text_answer = f"""
👤 <b>Информация о пользователе:</b>
<a href='tg://user?id={user.id}'>{user.first_name} {user.last_name or ''}</a> 
{'(@' + user.username + ')' if user.username else ''}
ID: <code>{user.id}</code>
{'-'*30}
{dc_info}
Статус: {status}
{phone}
Бот: {bot_status}
{lang}
{'-'*30}
Джарвис подключен: {jarvis_connected}
Рейтинг: {rating}%
"""
    await jarvis.send_message(message, text_answer)

async def handle_group_info(jarvis, message, chat):
    if isinstance(chat, types.Channel):
        chat_type = "Канале" if not chat.megagroup else "Супергруппа"
    else:
        chat_type = "Группе"

    participants = (await jarvis.client.get_participants(chat, limit=0)).total
    messages_count = (await jarvis.client.get_messages(chat, limit=0)).total
    created = chat.date.strftime("%d.%m.%Y") if chat.date else "Неизвестно"
    username = f"@{chat.username}" if chat.username else "Нет"
    link = f"https://t.me/{chat.username}" if chat.username else "Нет"

    text_answer = f"""
👥 <b>Информация о {chat_type.lower()}:</b>
{chat.title}
{'-'*30}
Тип: {chat_type}
ID: <code>{chat.id}</code>
Юзернейм: {username}
Участников: {participants}
Сообщений: {messages_count}
Дата создания: {created}
{'-'*30}
Ссылка: {link}
"""
    await jarvis.send_message(message, text_answer)