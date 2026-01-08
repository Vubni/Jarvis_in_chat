from database.database import Database
from aiogram.types import (
    InputMediaDocument, InputMediaPhoto, InputMediaVideo,
    InlineKeyboardMarkup as IMarkup,
    InlineKeyboardButton as IButton
)
from aiogram.utils.chat_action import ChatActionSender
from create_bot import bot
from typing import List, Tuple, Union
import config
import asyncio
import s3, random
from config import logger
from aiogram.types import URLInputFile
from telethon import types
from keyboards import telegram_client as kb

from bs4 import BeautifulSoup

def clean_html(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=' ', strip=True)



def message_count(number: int) -> str:
    """Форматирование количества сообщений с учетом склонения"""
    if number % 10 == 1 and number % 100 != 11:
        return f"{number} сообщение"
    elif number % 10 in [2, 3, 4] and number % 100 not in [12, 13, 14]:
        return f"{number} сообщение"
    return f"{number} сообщений"

async def delete_objects(media_contents):
    await asyncio.sleep(60)
    for item in media_contents:
        if not await s3.delete_object(item):
            logger.warning(f"Не удалось удалить объект из s3: {item}")

async def deleted_notification(jarvis, ids: List[int], event):
    """Обработка уведомлений об удаленных сообщениях"""
    chat = None
    text_all = ""
    text_all_array = []
    documents = []
    photos = []
    videos = []
    voices = []
    video_notes = []
    media_contents = []
    
    async with Database() as db:
        if isinstance(event.original_update, types.UpdateDeleteChannelMessages):
            results = await db.execute_all(
                "SELECT * FROM messages WHERE message_id = ANY($1) AND user_id = $2 AND chat_id = $3",
                (ids, jarvis.user.id, event.original_update.channel_id)
            )
        else:
            results = await db.execute_all(
                "SELECT * FROM messages WHERE message_id = ANY($1) AND user_id = $2",
                (ids, jarvis.user.id)
            )
        if not results:
            return
        
        chats = set()
        for result in results:
            chats.add(result["chat_id"])
        if len(chats) > 1:
            indx = -1
            for _chat in chats:
                indx += 1
                if _chat:
                    chat = await jarvis.client.get_entity(_chat)
                    if isinstance(chat, types.Channel):
                        chat = None
                        continue
                    if not jarvis.subscription:
                        await send_texts(None, await decrypt_message_text(db, results[indx]["id"]), ids, None, None, jarvis, chat)
                    break
        elif not chat and results[0]["chat_id"]:
            chat = await jarvis.client.get_entity(results[0]["chat_id"])
            if not jarvis.subscription:
                await send_texts(None, await decrypt_message_text(db, results[0]["id"]), ids, None, None, jarvis, chat)
        
        # Получаем данные первого сообщения для заголовка
        first_result = results[0]
        item = build_header_group if chat else build_header
        markup, header_text = await item(
            first_result["user_firstname"],
            first_result.get("username"),
            first_result["from_user_id"],
            len(results), 
            chat
        )

        for result in results:
            if chat and chat.id != result["chat_id"]:
                continue
            if not should_process_message(jarvis, result, chat):
                continue
                
            text_old = await decrypt_message_text(db, result["id"])
            if chat:
                text_old = f"<a href=tg://user?id={result['from_user_id']}>" + result["user_firstname"] + "</a>: " + text_old
            await db.execute("DELETE FROM messages WHERE id = $1", (result["id"],))
            
            media_content = result.get("media_content", "")
            if not media_content:
                text_block = f"<blockquote expandable>{text_old}</blockquote>\n\n"
                text_all += text_block
                text_all_array.append(text_block)
            else:
                media_contents.append(await categorize_media(media_content, text_old, documents, photos, videos, video_notes, voices))
    
    # Добавляем кнопку настроек
    markup.append([IButton(text='⚙️Настройки оповещений в лс', callback_data='start_bot_need')])
    
    # Отправка данных
    await send_texts(jarvis.user.id, text_all, text_all_array, markup, header_text, jarvis, chat)
    await send_media(jarvis.user.id, documents, photos, videos, video_notes, voices, jarvis, chat)
    if media_contents:
        asyncio.create_task(delete_objects(media_contents))

async def decrypt_message_text(db: Database, message_id: int) -> str:
    """Дешифровка текста сообщения"""
    query = "SELECT pgp_sym_decrypt(text::bytea, $1) AS text FROM messages WHERE id = $2"
    result = await db.execute(query, (config.KEY_ENCRYPTION, message_id))
    return result["text"] if result else ""

def should_process_message(jarvis, result: dict, chat=None) -> bool:
    """Проверка необходимости обработки сообщения"""
    for item in jarvis.settings["func_except"]:
        if item["id"] == result["from_user_id"]:
            return item.get("del", True)
    if chat:
        return jarvis.settings["groups"].get("del", False)
    return jarvis.settings["chats"].get("del", False)

async def build_header(name: str, username: str, user_id: int, count: int, chat=None) -> Tuple[List[list], str]:
    """Формирование заголовка уведомления"""
    markup = []
    url = f'tg://user?id={user_id}'  # Fallback URL
    
    if username:
        url = f'https://t.me/{username}'
    text = f"В личной переписке с '<a href='{url}'>{name}</a>' были удалены сообщения."
    
    try:
        # Проверяем доступность пользователя
        await bot.get_chat(user_id)
        markup.append([IButton(text='📬Перейти в личную переписку', url=url)])
    except Exception as e:
        markup.append([IButton(text='Кнопка перехода не создана. Почему?', callback_data='start_bot_need')])
    
    header = f"{text}\n\n<b>🗑️Было удалено {message_count(count)}</b>"
    return markup, header

async def build_header_group(name: str, username: str, user_id: int, count: int, chat: Union[types.Chat, types.Channel]) -> Tuple[List[list], str]:
    """Формирование заголовка уведомления"""
    markup = []
    url = f'https://t.me/{chat.id}/0'  # Fallback URL
    
    try:
        if chat.username:
            url = f'https://t.me/{chat.username}'
    except:
        pass
    text = f"В группе '<a href='{url}'>{chat.title}</a>' были удалены сообщения."
        
    markup.append([IButton(text='📬Перейти в группу', url=url)])
    header = f"{text}\n\n<b>🗑️Было удалено {message_count(count)}</b>"
    return markup, header

async def categorize_media(media_content: str, text_old: str, 
                    documents: list, photos: list, 
                    videos: list, video_notes: list, 
                    voices: list):
    """Классификация медиафайлов"""
    media_type, _, media_file = media_content.partition("=")
    media_file = media_file.split("|")
    media_url = await s3.generate_presigned_url(f"files/{media_file[0]}")
    
    if media_type == "document":
        documents.append((media_url, text_old, media_file[1]))
    
    elif media_type in ['photo', 'video']:
        # Для этих типов передаем кортеж (URL, caption)
        {   'photo': photos,
            'video': videos
        }[media_type].append((media_url, text_old))
    
    elif media_type in ['voice', 'video_note']:
        # Для этих типов caption не поддерживается
        {   'voice': voices,
            'video_note': video_notes
        }[media_type].append(media_url)
    return f"files/{media_file[0]}"

async def send_texts(user_id: int, text_all: str, text_all_array: List[str], 
                    markup: list, header_text: str, jarvis, chat:Union[types.Chat, types.Channel]=None):
    """Отправка текстовых сообщений с разбивкой на части"""
    
    if not jarvis.subscription and chat:
        if chat.left:
            return
        if random.choice([True, False]):
            url = f'https://t.me/{chat.id}/0'
            try:
                if chat.username:
                    url = f'https://t.me/{chat.username}'
            except:
                pass
            text = f"В группе '<a href='{url}'>{chat.title}</a>' были удалены сообщения."
            header_text = f"{text}\n\n<b>🗑️Было удалено {message_count(len(text_all_array))}</b>"
            async with Database() as db:
                text = clean_html(text_all)
                if text:
                    text = text[:3] if len(text) > 3 else ""
                    await bot.send_message(jarvis.user.id, header_text + f"🗑️Было удалено 1 сообщение, оно содержало:\n<blockquote>{text + ('*' * random.randint(4, 10))}</blockquote>\n\n"
                                "<i>Чтобы видеть удалённые сообщения <b>в группах</b> в будущем, нужно приобрести подписку!</i>", reply_markup=kb.ad_pro(chat.id), disable_notification=True, disable_web_page_preview=True)
        return
    try:
        if len(header_text) + len(text_all) < 4096:
            await bot.send_message(
                user_id,
                header_text + "\n\n" + text_all,
                reply_markup=IMarkup(inline_keyboard=markup),
                disable_notification=True,
                disable_web_page_preview=True
            )
        else:
            current_text = header_text
            for text_block in text_all_array:
                if len(current_text) + len(text_block) > 4096:
                    await bot.send_message(user_id, current_text, reply_markup=IMarkup(inline_keyboard=markup))
                    current_text = ""
                current_text += text_block
            if current_text:
                await bot.send_message(user_id, current_text, reply_markup=IMarkup(inline_keyboard=markup))
    except Exception as e:
        if "BUTTON_USER_PRIVACY_RESTRICTED" in str(e):
            markup[0] = [IButton(text='Кнопка перехода не создана. Почему?', callback_data='start_bot_need')]
            return await send_texts(user_id, text_all, text_all_array, markup, header_text, jarvis, chat)
        logger.error(f"Ошибка при отправке текста: {e}")

async def send_media(user_id: int, documents: List[Tuple], photos: List[Tuple], 
                    videos: List[Tuple], video_notes: List[str], 
                    voices: List[str], jarvis, chat=None):
    """Отправка медиафайлов"""
    
    if not jarvis.subscription and chat:
        return
    
    await send_media_group(user_id, documents, InputMediaDocument, ChatActionSender.upload_document)
    await send_media_group(user_id, photos, InputMediaPhoto, ChatActionSender.upload_photo)
    await send_media_group(user_id, videos, InputMediaVideo, ChatActionSender.upload_video)
    
    if video_notes:
        async with ChatActionSender.upload_video(user_id, bot):
            for note in video_notes:
                try:
                    await bot.send_video_note(user_id, note, disable_notification=True)
                except Exception as e:
                    logger.error(f"Ошибка при отправке video_note: {e}")
    
    if voices:
        async with ChatActionSender.record_voice(user_id, bot):
            for voice in voices:
                try:
                    await bot.send_voice(user_id, voice, disable_notification=True)
                except Exception as e:
                    logger.error(f"Ошибка при отправке voice: {e}")

async def send_media_group(user_id: int, media_list: list, 
                         media_type, action_sender):
    """Универсальная функция отправки медиагрупп"""
    if not media_list:
        return
    
    async with action_sender(user_id, bot):
        if len(media_list) == 1:
            if media_type == InputMediaDocument:
                media, caption, filename = media_list[0]
                await bot.send_document(user_id, URLInputFile(media, filename=filename), caption=caption)
            elif media_type == InputMediaPhoto:
                media, caption = media_list[0]
                await bot.send_photo(user_id, media, caption=caption)
            elif media_type == InputMediaVideo:
                media, caption = media_list[0]
                await bot.send_video(user_id, media, caption=caption)
            return
        medias = []
        for item in media_list:
            media, caption = item
            if media_type == InputMediaDocument:
                medias.append(media_type(media=URLInputFile(media), caption=caption))
            else:
                medias.append(media_type(media=media, caption=caption))
        
        for i in range(0, len(medias), 10):
            try:
                await bot.send_media_group(
                    user_id,
                    medias[i:i+10],
                    disable_notification=True
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке медиагруппы: {e}")