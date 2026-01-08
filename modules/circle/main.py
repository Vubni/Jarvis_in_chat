from functions.functions import My_message
from TelegramClient import Jarvis_client
from telethon.tl.patched import Message
import os, string, random
import ffmpeg
from modules.circle.settings import PATH
from config import jarvis_all, data_users

status = True

def generate_random_name():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(10))

def crop_video_to_square(input_path, output_path):
    try:
        probe = ffmpeg.probe(input_path)
        video_info = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
        width = int(video_info['width'])
        height = int(video_info['height'])

        if width > height:
            x = (width - height) // 2
            y = 0
            size = height
        else:
            x = 0
            y = (height - width) // 2
            size = width

        input_stream = ffmpeg.input(input_path)
        video_stream = (
            input_stream.video
            .crop(x, y, size, size)
            .filter('scale', 600, 600)
        )

        audio_stream = None
        for stream in probe['streams']:
            if stream['codec_type'] == 'audio':
                audio_stream = input_stream.audio
                break

        if audio_stream is not None:
            output = ffmpeg.output(
                video_stream,
                audio_stream,
                output_path,
                vcodec='libx264',
                acodec='aac'
            )
        else:
            output = ffmpeg.output(
                video_stream,
                output_path,
                vcodec='libx264'
            )

        output.overwrite_output().run(quiet=True)

    except Exception as e:
        print(f"Ошибка при обработке видео: {e}")
        raise  # Пробрасываем исключение для обработки выше
    
def get_video_duration_ffprobe(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        # Пытаемся получить длительность из формата
        duration = float(probe['format'].get('duration', 0))
        
        # Если в формате нет, проверяем видео потоки
        if duration <= 0:
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            if video_stream:
                duration = float(video_stream.get('duration', 0))
        
        return duration if duration > 0 else None
    except Exception as e:
        print(f"Ошибка при получении информации о видео: {e}")
        return None

async def start(jarvis: Jarvis_client, new_message: My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]:
        return
    message = new_message.message
    text = message.text.lower()
    
    if text not in ["сделать кружок", "сделай кружок", "в кружок", "хочу кружок", "создай кружок", "создать кружок", "преобразовать в кружок"]:
        return

    try:
        # Определяем сообщение с видео
        if message.is_reply:
            video_message = await message.get_reply_message()
            if not (video_message.media and video_message.media.video):
                return
        else:
            if not (message.media and message.media.video):
                return
            video_message = message

        msg = await jarvis.send_message(message, "Преобразую видео. . .")
        code = generate_random_name()
        filename = f"temp_output/{code}.mp4"
        
        # Скачиваем видео
        file_path = await jarvis.client.download_media(video_message.media, file=filename)
        if not file_path or not os.path.exists(file_path):
            await msg.delete()
            await jarvis.send_message(message, "Не удалось скачать видео.")
            return

        # Проверяем длительность
        duration = get_video_duration_ffprobe(file_path)
        if duration is None:
            await msg.delete()
            await jarvis.send_message(message, "Не удалось определить длительность видео.")
            return
            
        if duration > 60:
            os.remove(file_path)
            await msg.delete()
            await jarvis.send_message(message, "Видео должно быть короче 1 минуты!")
            return

        # Проверяем размер файла
        if os.path.getsize(file_path) > 20 * 1024 * 1024:
            os.remove(file_path)
            await msg.delete()
            await jarvis.send_message(message, "Видео должно быть меньше 20 МБ!")
            return

        # Обрабатываем видео
        output_filename = f"temp_output/circle_{code}.mp4"
        try:
            crop_video_to_square(file_path, output_filename)
        except Exception as e:
            await msg.delete()
            await jarvis.send_message(message, f"Ошибка обработки видео: {str(e)}")
            return

        # Отправляем результат
        await jarvis.client.delete_messages(message.chat_id, msg.id)
        await jarvis.client.send_file(message.chat_id, output_filename, video_note=True)

    finally:
        # Удаляем временные файлы
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        if 'output_filename' in locals() and os.path.exists(output_filename):
            os.remove(output_filename)