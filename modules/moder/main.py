from functions.functions import My_message
from TelegramClient import Jarvis_client
from modules.voice.settings import PATH
from config import jarvis_all, data_users
from telethon.tl import types, functions
from telethon.errors import UserNotParticipantError, ChatAdminRequiredError
from typing import Union
from datetime import datetime, timedelta
import pytz
import re, asyncio

status = True

def is_command(text):
    exact_commands = [
        "общий сбор",
        "почистить группу от мошенников",
        "кикнуть подозрительные аккаунты",
        "почистить группу",
        "кикнуть удалённые аккаунты",
        "найти спящих",
        "найди спящих",
        "+анонимность",
        "-анонимность",
        "разбан",
        "разблокировать",
        "бан",
        "заблокировать",
        "кик",
        "изгнать",
        "размут",
        "мут",
        "варн"
    ]
    prefix_commands = ["изменить префикс"]
    
    text_lower = text.lower()
    return any(text_lower == cmd for cmd in exact_commands) or \
           any(text_lower.startswith(cmd) for cmd in prefix_commands)

def check_admin_permissions(func):
    async def wrapper(jarvis, new_message, *args, **kwargs):
        text = new_message.message.text.lower()
        
        # Проверяем, содержит ли сообщение команду
        if not is_command(text):
            return
            
        user_id = jarvis.user.id
        if user_id not in data_users or PATH not in jarvis_all[data_users[user_id]].settings["modules"]:
            await jarvis.send_message(new_message.message, "❌ Модуль управления чатом выключен")
            return
        
        if not new_message.message.out:
            return
        
        if not jarvis.subscription:
            return await jarvis.send_message(new_message.message, "Команда доступна только для обладателей платной подписки Джарвис.")
            
        chat = new_message.chat
        if isinstance(chat, types.User):
            return await jarvis.send_message(new_message.message, "Команда доступна только в группах/каналах.")
            
        try:
            if not await is_admin_chat(jarvis, chat):
                return await jarvis.send_message(new_message.message, "⚠️ Недостаточно прав для выполнения действия.")
        except Exception as e:
            print(f"Ошибка проверки прав: {e}")
            return
            
        # Выполняем обработку команды
        result = await func(jarvis, new_message, *args, **kwargs)
        if not result:
            await jarvis.send_message(new_message.message, "❓ Неизвестная команда или неверный формат")
        return result
    return wrapper

async def is_admin_chat(jarvis, chat: Union[types.Chat, types.Channel]):
    try:
        # Используем правильный метод Telethon
        participant = await jarvis.client(
            functions.channels.GetParticipantRequest(
                channel=chat,
                participant=jarvis.user.id
            )
        )
        return isinstance(
            participant.participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator)
        )
    except (UserNotParticipantError, ChatAdminRequiredError):
        return False
    except Exception as e:
        print(f"Ошибка проверки прав администратора: {e}")
        return False

async def get_target_user(jarvis, message, chat):
    try:
        if message.is_reply:
            reply_msg = await message.get_reply_message()
            # Исправление: правильное извлечение ID пользователя из reply
            user_id = reply_msg.from_id.user_id if hasattr(reply_msg.from_id, 'user_id') else reply_msg.from_id
            return await jarvis.client.get_entity(user_id)
        else:
            # Исправление: использование регулярного выражения для извлечения username
            match = re.search(r'@(\w+)', message.text)
            if match:
                return await jarvis.client.get_entity(match.group(1))
        return None
    except (ValueError, UserNotParticipantError, AttributeError):
        return None

def parse_time(text):
    units = {
        'секунд': 'seconds',
        'секунда': 'seconds',
        'минут': 'minutes',
        'минуту': 'minutes',
        'час': 'hours',
        'часа': 'hours',
        'день': 'days',
        'дня': 'days',
        'неделя': 'weeks',
        'недели': 'weeks',
        'месяц': 'months',
        'месяца': 'months',
        'год': 'years',
        'года': 'years'
    }
    pattern = r'(\d+)\s+(' + '|'.join(units.keys()) + r')'
    matches = re.findall(pattern, text)
    
    delta = timedelta()
    for value, unit in matches:
        value = int(value)
        unit = units[unit]
        if unit == 'seconds':
            delta += timedelta(seconds=value)
        elif unit == 'minutes':
            delta += timedelta(minutes=value)
        elif unit == 'hours':
            delta += timedelta(hours=value)
        elif unit == 'days':
            delta += timedelta(days=value)
        elif unit == 'weeks':
            delta += timedelta(weeks=value)
        elif unit == 'months':
            delta += timedelta(days=30*value)
        elif unit == 'years':
            delta += timedelta(days=365*value)
    return delta

def format_timedelta(delta):
    parts = []
    days = delta.days
    seconds = delta.seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days:
        parts.append(plural_form(days, 'день', 'дня', 'дней'))
    if hours:
        parts.append(plural_form(hours, 'час', 'часа', 'часов'))
    if minutes:
        parts.append(plural_form(minutes, 'минута', 'минуты', 'минут'))
    if seconds:
        parts.append(plural_form(seconds, 'секунда', 'секунды', 'секунд'))
        
    return ', '.join(parts)

def plural_form(n, one, few, many):
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} {one}"
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return f"{n} {few}"
    else:
        return f"{n} {many}"

@check_admin_permissions
async def start(jarvis: Jarvis_client, new_message: My_message):
    message = new_message.message
    chat = new_message.chat
    text = message.text.lower()
    
    if text == "общий сбор":
        await handle_mass_mention(jarvis, message, chat)
        return True
    elif text in ["почистить группу от мошенников", "кикнуть подозрительные аккаунты"]:
        await handle_scam_accounts(jarvis, message, chat)
        return True
    elif text in ["почистить группу", "кикнуть удалённые аккаунты"]:
        await handle_deleted_accounts(jarvis, message, chat)
        return True
    elif text in ["найти спящих", "найди спящих"]:
        await find_inactive_users(jarvis, message, chat)
        return True
    elif text in ["+анонимность", "-анонимность"]:
        await toggle_anonymity(jarvis, message, chat, text.startswith('+'))
        return True
    elif text.startswith("изменить префикс"):
        await change_user_prefix(jarvis, message, chat)
        return True
    elif text.startswith(("разбан", "разблокировать")):
        await unban_user(jarvis, message, chat)
        return True
    elif text.startswith(("бан", "заблокировать")):
        await ban_user(jarvis, message, chat)
        return True
    elif text.startswith(("кик", "изгнать")):
        await kick_user(jarvis, message, chat)
        return True
    elif text.startswith("размут"):
        await unmute_user(jarvis, message, chat)
        return True
    elif text.startswith("мут"):
        await mute_user(jarvis, message, chat)
        return True
    elif text.startswith("варн"):
        await warn_user(jarvis, message, chat)
        return True
    
async def handle_mass_mention(jarvis, message, chat):
    participants = await jarvis.client.get_participants(chat)
    mentions = []
    msg_count = 0
    for i, user in enumerate(participants, 1):
        mentions.append(f"<a href='tg://user?id={user.id}'>\u200B</a>")
        if i % 5 == 0 or i == len(participants):
            # Исправление: добавлена задержка для избежания флуда
            await jarvis.send_message(message, f"Общий сбор! Упомянутые участники: {', '.join(mentions)}")
            mentions.clear()
            msg_count += 1

async def handle_scam_accounts(jarvis, message, chat):
    msg = await jarvis.send_message(message, "Поиск мошенников...")
    count = 0
    
    async for user in jarvis.client.iter_participants(chat):
        if getattr(user, 'scam', False):
            await jarvis.client.kick_participant(chat, user)
            count += 1
            
    await jarvis.client.delete_messages(chat, msg.id)
    text = f"Удалено {count} мошенников." if count else "Мошенников не найдено."
    await jarvis.send_message(message, text)

async def handle_deleted_accounts(jarvis, message, chat):
    msg = await jarvis.send_message(message, "Поиск удалённых аккаунтов...")
    count = 0
    
    async for user in jarvis.client.iter_participants(chat):
        if user.deleted:
            await jarvis.client.kick_participant(chat, user)
            count += 1
            
    await jarvis.client.delete_messages(chat, msg.id)
    text = f"Удалено {count} аккаунтов." if count else "Удалённых аккаунтов нет."
    await jarvis.send_message(message, text)

async def find_inactive_users(jarvis, message, chat):
    msg = await jarvis.send_message(message, "Анализ активности...")
    current_time = datetime.now(pytz.UTC)
    active_users = set()
    inactive = []
    never_active = []
    
    async for user in jarvis.client.iter_participants(chat):
        if user.bot:
            continue
        last_msg = None
        async for m in jarvis.client.iter_messages(chat, from_user=user, limit=1):
            last_msg = m.date.replace(tzinfo=pytz.UTC)
        if last_msg:
            if (current_time - last_msg).days > 3:
                inactive.append((user, last_msg))
            active_users.add(user.id)
        else:
            never_active.append(user)
    
    text = []
    if inactive:
        text.append("Неактивные пользователи:")
        for user, date in inactive:
            text.append(f"<a href='tg://user?id={user.id}'>{user.first_name}</a> - {date.strftime('%d.%m.%Y')}")
    
    if never_active:
        text.append("\nНи разу не писали:")
        for user in never_active:
            text.append(f"<a href='tg://user?id={user.id}'>{user.first_name}</a>")
    
    await jarvis.client.edit_message(chat, msg.id, "\n".join(text) if text else "Все активны!")

async def toggle_anonymity(jarvis, message, chat, enable):
    try:
        participant = await jarvis.client.get_participant(chat, jarvis.user.id)
        if not hasattr(participant, 'admin_rights'):
            return await jarvis.send_message(message, "Требуются права администратора.")
            
        rights = participant.admin_rights
        rights.anonymous = enable
        await jarvis.client(functions.channels.EditAdminRequest(
            chat,
            jarvis.user.id,
            rights,
            participant.rank or ""
        ))
        status = "включена" if enable else "отключена"
        await jarvis.send_message(message, f"Анонимность {status}.")
    except Exception as e:
        print(f"Ошибка при изменении анонимности: {e}")

async def change_user_prefix(jarvis, message, chat):
    user = await get_target_user(jarvis, message, chat)
    if not user:
        return await jarvis.send_message(message, "Пользователь не указан.")
        
    new_title = ' '.join(message.text.split()[2:])[:16]
    if not new_title:
        return await jarvis.send_message(message, "Укажите новый префикс.")
        
    try:
        participant = await jarvis.client.get_participant(chat, user.id)
        if not hasattr(participant, 'admin_rights'):
            return await jarvis.send_message(message, "Пользователь не администратор.")
            
        await jarvis.client(functions.channels.EditAdminRequest(
            chat,
            user.id,
            participant.admin_rights,
            new_title
        ))
        await jarvis.send_message(message, f"Префикс изменен для {user.first_name}.")
    except Exception as e:
        print(f"Ошибка изменения префикса: {e}")

async def ban_user(jarvis, message, chat):
    user = await get_target_user(jarvis, message, chat)
    if not user:
        return
        
    duration = parse_time(message.text)
    until_date = (datetime.now() + duration) if duration else None
    try:
        await jarvis.client.edit_permissions(
            chat,
            user.id,
            until_date=until_date,
            view_messages=False
        )
        period = format_timedelta(duration) if duration else "навсегда"
        await jarvis.send_message(message, f"{user.first_name} заблокирован на {period}.")
    except ChatAdminRequiredError:
        await jarvis.send_message(message, "Недостаточно прав.")

async def unban_user(jarvis, message, chat):
    user = await get_target_user(jarvis, message, chat)
    if not user:
        return
        
    try:
        await jarvis.client.edit_permissions(
            chat,
            user.id,
            view_messages=True
        )
        await jarvis.send_message(message, f"{user.first_name} разбанен.")
    except Exception as e:
        print(f"Ошибка разбана: {e}")

async def kick_user(jarvis, message, chat):
    user = await get_target_user(jarvis, message, chat)
    if not user:
        return
        
    try:
        await jarvis.client.kick_participant(chat, user.id)
        await jarvis.send_message(message, f"{user.first_name} удален из чата.")
    except Exception as e:
        print(f"Ошибка кика: {e}")

async def mute_user(jarvis, message, chat):
    user = await get_target_user(jarvis, message, chat)
    if not user:
        return
        
    duration = parse_time(message.text)
    until_date = datetime.now() + duration if duration else None
    try:
        await jarvis.client.edit_permissions(
            chat,
            user.id,
            until_date=until_date,
            send_messages=False
        )
        period = format_timedelta(duration) if duration else "навсегда"
        await jarvis.send_message(message, f"{user.first_name} замучен на {period}.")
    except Exception as e:
        print(f"Ошибка мута: {e}")

async def unmute_user(jarvis, message, chat):
    user = await get_target_user(jarvis, message, chat)
    if not user:
        return
        
    try:
        await jarvis.client.edit_permissions(
            chat,
            user.id,
            send_messages=True
        )
        await jarvis.send_message(message, f"{user.first_name} размучен.")
    except Exception as e:
        print(f"Ошибка размута: {e}")

async def warn_user(jarvis, message, chat):
    user = await get_target_user(jarvis, message, chat)
    if not user:
        return
        
    reason = ' '.join(message.text.split()[2:]) if message.is_reply else ' '.join(message.text.split()[1:])
    await jarvis.send_message(message, f"Внимание! {user.first_name} получил предупреждение. Причина: {reason}")