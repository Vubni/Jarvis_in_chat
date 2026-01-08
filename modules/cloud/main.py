from functions.functions import My_message
from TelegramClient import Jarvis_client
from database.database import Database
from telethon.tl import types
import os
import uuid
from config import jarvis_all, data_users
from modules.cloud.settings import PATH
import s3
from functions.functions import clean_html

status = True

async def start(jarvis: Jarvis_client, my_message: My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]:
        return

    message = my_message.message
    text = message.text.lower()
    if text.startswith(("сохрани", "сохранить")) and len(text.split()) > 1:
        if message.is_reply:
            reply_message = my_message.reply_message
            name = text.split()[1]
            async with Database() as db:
                res = await db.execute("SELECT id FROM saved_messages WHERE user_id=$1 and name=$2", (jarvis.user.id, name))
                if res:
                    return await jarvis.send_message(message, f"Запись в облаке с названием '{name}' уже существует!")
            if not reply_message.media and not reply_message.photo and not reply_message.document:
                async with Database() as db:
                    await db.execute("INSERT INTO saved_messages (user_id, name, text) VALUES ($1, $2, $3)", (jarvis.user.id, name, reply_message.text))
                    return await jarvis.send_message(message, f"<b>Сообщение успешно сохранено!</b>\nТеперь оно доступно под названием '<code>{name}</code>'!")
                    
            else:
                print(reply_message, "\n----------------------------------")
                media_type = 'unknown'
                if reply_message.photo:
                    media_type = "photo"
                elif reply_message.video:
                    media_type = "video"
                elif reply_message.voice:
                    media_type = "voice"
                elif reply_message.document:
                    media_type = "document"

                mime_type = None
                if media_type == 'document':
                    document = reply_message.media.document
                    file_name = None
                    file_size = document.size
                    mime_type = document.mime_type
                    if mime_type not in ["application/pdf", "application/zip"]:
                        return await jarvis.send_message(message, f"<b>Файл не может быть сохранён!</b>\nК сожалению, Telegram позволяет сохранять только файлы формата .pdf и .zip!")
                    for attr in document.attributes:
                        if isinstance(attr, types.DocumentAttributeFilename):
                            file_name = attr.file_name
                            break
                    if not file_name:
                        await jarvis.send_message(message, "Не удалось определить имя файла.")
                        return
                    extension = os.path.splitext(file_name)[1]
                elif media_type == 'photo':
                    file_size = max(reply_message.photo.sizes[-1].sizes)
                    extension = '.jpg'
                elif media_type == 'video':
                    file_size = reply_message.video.size
                    extension = '.mp4'
                elif media_type == 'voice':
                    file_size = reply_message.voice.attributes[0].duration * 16000
                    extension = '.ogg'
                else:
                    await jarvis.send_message(message, "Не поддерживаемый тип медиа.")
                    return

                if file_size > 20 * 1024 * 1024 and not jarvis.subscription:
                    await jarvis.send_message(message, "Файл весит более лимита в 20 Мбайт!\n\nЧтобы увеличить лимит до 1гб - обновитесь до Джарвис Pro")
                    return

                media_bytes = await jarvis.client.download_media(reply_message.media, bytes)
                s3_key = f"{uuid.uuid4().hex}{extension}"
                await s3.upload_bytes(media_bytes, "cloud/" + s3_key, mime_type)

                content = f"{media_type}={s3_key}"
                async with Database() as db:
                    await db.execute("INSERT INTO saved_messages (user_id, name, text, content) VALUES ($1, $2, $3, $4)", (jarvis.user.id, name, clean_html(reply_message.text), content))
                return await jarvis.send_message(message, f"<b>Сообщение успешно сохранено!</b>\nТеперь оно доступно под названием '<code>{name}</code>'!")