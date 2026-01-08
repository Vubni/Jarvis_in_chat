from functions.functions import My_message
from TelegramClient import Jarvis_client
from telethon.tl.patched import Message
from config import jarvis_all, data_users
from modules.recognize.settings import PATH
import os
import io
import json
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment

model = Model("Vosk")  # Укажите путь к модели Vosk

status = True
status_start = {}

async def start(jarvis: Jarvis_client, new_message: My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]:
        return

    message = new_message.message
    text = message.text.lower()
    reply_message = new_message.reply_message

    if ("распозна" in text or "что в аудио" in text or "напиши" in text or "не могу слушать" in text) and reply_message and reply_message.media:
        await message.edit(text="Начинаю распознавание...")

        try:
            # Скачиваем медиа в память
            media_bytes = await jarvis.client.download_media(reply_message.media, bytes)
            mime_type = reply_message.file.mime_type

            # Определяем тип медиа
            if mime_type.startswith('audio/'):
                if mime_type == 'audio/ogg':
                    audio = AudioSegment.from_file(io.BytesIO(media_bytes), format="ogg")
                elif mime_type == 'audio/mpeg':
                    audio = AudioSegment.from_file(io.BytesIO(media_bytes), format="mp3")
                else:
                    raise ValueError("Неподдерживаемый аудиоформат")
                    
            elif mime_type.startswith('video/'):
                if mime_type == 'video/mp4':
                    audio = AudioSegment.from_file(io.BytesIO(media_bytes), format="mp4")
                elif mime_type == 'video/webm':
                    audio = AudioSegment.from_file(io.BytesIO(media_bytes), format="webm")
                else:
                    raise ValueError("Неподдерживаемый видеоформат")
            else:
                return await message.edit(text="Неподдерживаемый тип медиа")

            # Продолжаем обработку аудио
            audio = audio.set_frame_rate(16000) \
                         .set_channels(1) \
                         .set_sample_width(2)
            
            # Проверка длительности
            total_length = len(audio)
            if total_length > 10 * 60 * 1000 and not jarvis.subscription:
                return await message.edit(text="Аудиофайл длится больше 10 минут! Требуется Pro подписка!")
            
            # Разбиваем на части по 30 секунд
            max_audio_length = 30 * 1000  # 30 секунд
            segments = []
            for i in range(0, total_length, max_audio_length):
                segment = audio[i:i + max_audio_length]
                segments.append(segment)
            
            full_transcript = ""
            recognizer = KaldiRecognizer(model, 16000)
            
            for idx, segment in enumerate(segments):
                # Конвертируем сегмент в байты WAV
                wav_bytes = segment.export(format="wav").read()
                
                # Распознаём речь
                recognizer.AcceptWaveform(wav_bytes)
                result = json.loads(recognizer.Result())
                full_transcript += result.get("text", "").strip() + " "
                
                # Обновляем прогресс
                await message.edit(text=f"Распознано {idx+1}/{len(segments)} частей: <blockquote expandable>{full_transcript[:50]}...</blockquote>")

            # Получаем финальный результат
            final_result = json.loads(recognizer.FinalResult())
            full_transcript += final_result.get("text", "").strip()

            await message.edit(text=f"Аудио содержит: <blockquote expandable>{full_transcript.strip()}</blockquote>")
        except Exception as e:
            print("Ошибка распознавания:", e)
            await message.edit(text=f"Ошибка: {str(e)}")