from functions.functions import My_message
from TelegramClient import Jarvis_client
from modules.voice.settings import PATH
from config import jarvis_all, data_users
from pydub import AudioSegment
from telethon.tl.types import DocumentAttributeFilename
import os
import tempfile

status = True

def get_media_extension(media):
    if hasattr(media, 'document'):
        for attr in media.document.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                ext = os.path.splitext(attr.file_name)[1].lower()
                return ext[1:] if ext else None
    return None

def convert_audio_to_ogg(input_path: str, output_path: str) -> None:
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="ogg", codec="libopus")
    except Exception as e:
        raise RuntimeError(f"Ошибка конвертации: {e}")

async def start(jarvis: Jarvis_client, new_message: My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]:
        return
    message = new_message.message
    text = message.text.lower()
    
    if text in ["сделать гс", "сделай гс", "сделать в гс", "сделай в гс", "сделать голосовое", "создай гс", "сделай голосовое", "сделать голосовое сообщение", "в гс", "хочу гс"]:
        if message.is_reply:
            reply_message = await message.get_reply_message()
            if not reply_message.media:
                return
            if not reply_message.media.video and not reply_message.media.round:
                msg = await jarvis.send_message(message, "Преобразую аудио. . .")
                try:
                    # Создаем временные файлы
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp_input, \
                         tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_output:
                        
                        # Скачиваем файл на диск
                        input_path = await jarvis.client.download_media(reply_message.media, tmp_input.name)
                        media_ext = get_media_extension(reply_message.media)
                        
                        if not media_ext:
                            raise ValueError("Не удалось определить формат файла")
                        
                        # Конвертируем в OGG
                        convert_audio_to_ogg(input_path, tmp_output.name)
                        
                        # Отправляем как обычный файл (не voice_note)
                        await jarvis.client.send_file(
                            message.chat_id,
                            tmp_output.name,
                            voice_note=True,
                            attributes=[DocumentAttributeFilename("voice.ogg")]
                        )
                        
                        await jarvis.client.delete_messages(message.chat_id, msg.id)
                except Exception as e:
                    await jarvis.client.delete_messages(message.chat_id, msg.id)
                    await jarvis.send_message(message, f"Ошибка: {str(e)}")
                finally:
                    # Удаляем временные файлы
                    if os.path.exists(tmp_input.name):
                        os.remove(tmp_input.name)
                    if os.path.exists(tmp_output.name):
                        os.remove(tmp_output.name)