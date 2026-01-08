from functions.functions import My_message
from TelegramClient import Jarvis_client
from database.database import Database
from functions.functions import generate_random_name
from telethon.tl import types
import os
import qrcode, re
from PIL import Image, ImageDraw
from io import BytesIO
from config import jarvis_all, data_users
from modules.qr.settings import PATH

status = True


def contains_link(text):
    url_pattern = re.compile(
        r'\b((?:https?://)?(?:www\.)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s]*)?)\b',
        re.IGNORECASE
    )
    match = url_pattern.search(text)
    return match.group(0) if match else None


def create_qr_with_logo(url):
    # Создаем QR-код с минимальной границей (border=2)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=1,  # Уменьшаем границу вокруг QR-кода
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Генерируем изображение QR-кода
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Загружаем логотип и изменяем его размер
    logo = Image.open("images/logo.png").convert("RGBA")
    qr_width, qr_height = img.size

    # Логотип будет в 5 раз меньше QR-кода (немного меньше, чем раньше)
    logo_size = qr_width // 5
    logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

    # Создаем маску для логотипа, чтобы убрать черные полосы
    mask = Image.new("L", (logo_size, logo_size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, logo_size, logo_size), fill=255)  # Делаем логотип круглым (опционально)

    # Вычисляем позицию для центрирования логотипа
    logo_position = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)

    # Накладываем логотип на QR-код
    img_with_logo = Image.new("RGBA", img.size)
    img_with_logo.paste(img, (0, 0))
    img_with_logo.paste(logo, logo_position, mask=mask)  # Используем маску для улучшения внешнего вида

    # Конвертируем обратно в RGB (убираем альфа-канал)
    final_img = img_with_logo.convert("RGB")

    # Сохраняем результат в байтовый поток
    output = BytesIO()
    final_img.save(output, format="PNG")
    output.seek(0)
    output.name = "qr_code.png"

    return output

async def start(jarvis : Jarvis_client, my_message : My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]:
        return
    
    message = my_message.message
    text = message.text.lower()
    if ("создать qr" in text or "qr" == text[:2]) and len(text.split()) <= 4:
        url = contains_link(message.message)
        if not url and message.is_reply:
            reply_message = await message.get_reply_message()
            url = contains_link(reply_message.message)
        if url:
            return await jarvis.client.edit_message(my_message.chat, message, "", file=create_qr_with_logo(url), force_document=False)