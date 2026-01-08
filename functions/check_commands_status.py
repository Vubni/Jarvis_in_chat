from database.database import Database
import random
from create_bot import bot
from datetime import datetime, timedelta
import pytz
import config
from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton
from functions.messages import send_message_online
import asyncio

async def check_commands_status(jarvis):
    res = await search_commands_status(jarvis)
    if not res:
        return
    command = None
    for module in config.modules.values():
        if res == module["settings"].UNIQ_ID:
            command = module["settings"].NAME
    if not command:
        return
    inline_kb_list = [[IButton(text="Подробнее о команде", callback_data=res)]]
    asyncio.create_task(send_message_online(jarvis, bot.send_message(jarvis.user.id, f"Привет👋\nЯ заметил, что ты давно или ни разу не использовал(-а) команду <b>{command}</b>!\n\nВозможно ты просто не замечал(-а) её!", reply_markup=IMarkup(inline_keyboard=inline_kb_list))))
    

async def search_commands_status(jarvis):
    user_id = jarvis.user.id
    days_threshold = 3
    try:
        async with Database() as db:
            current_time = datetime.now(pytz.UTC)
            threshold_date = current_time - timedelta(days=days_threshold)

            # Получаем использованные команды с их последними датами
            commands = await db.execute_all("""
                SELECT command_id, MAX(used_date) as last_used
                FROM commands_usage
                WHERE user_id = $1
                GROUP BY command_id
            """, (user_id,))
            used_commands = {cmd["command_id"]: cmd["last_used"] for cmd in commands}

            all_commands = []
            for module in config.modules.values():
                all_commands.append(module["settings"].UNIQ_ID)
            unused_commands = [cmd for cmd in all_commands if cmd not in used_commands]

            # Если есть неиспользованные команды - возвращаем случайную
            if unused_commands:
                return random.choice(unused_commands)

            # Иначе ищем команды, не использовавшиеся более days_threshold дней
            else:
                # Фильтруем команды, которые использовались до пороговой даты
                old_commands = [
                    (cmd_id, last_used) 
                    for cmd_id, last_used in used_commands.items() 
                    if last_used < threshold_date
                ]
                
                # Если есть такие команды - возвращаем самую старую
                if old_commands:
                    # Находим команду с самой ранней датой последнего использования
                    oldest_cmd = min(old_commands, key=lambda x: x[1])[0]
                    return oldest_cmd
                else:
                    return None

    except Exception as e:
        print(f"Ошибка в check_commands_status: {e}")
        return None