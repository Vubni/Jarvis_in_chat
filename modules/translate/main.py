from functions.functions import My_message
from TelegramClient import Jarvis_client
from modules.translate.settings import PATH
from config import jarvis_all, data_users
import translators as ts
import re

status = True
# Словарь поддерживаемых языков
LANGUAGES = {
    "русский": "ru",
    "английский": "en",
    "французский": "fr",
    "немецкий": "de",
    "испанский": "es",
    "португальский": "pt",
    "итальянский": "it",
    "греческий": "el",
    "польский": "pl",
    "турецкий": "tr",
    "сербский": "sr",
    "украинский": "uk"
}

# Регулярное выражение для проверки русских букв
RUSSIAN_PATTERN = re.compile(r'^[а-яА-ЯёЁ]+$')

def is_russian_word(word):
    """Проверяет, состоит ли слово только из русских букв"""
    return bool(RUSSIAN_PATTERN.match(word))

def parse_translation_command(text):
    """Парсит команду перевода в формате 'переведи [на язык] [текст]'"""
    parts = text.split(maxsplit=3)
    if len(parts) < 3:
        return None, None, "Недостаточно параметров"
    
    # Определяем язык перевода
    lang_part = parts[2].lower()
    target_lang = LANGUAGES.get(lang_part)
    
    # Если язык не найден, предполагаем что это часть текста
    if not target_lang:
        return parts[1], ' '.join(parts[2:]), None
    
    return target_lang, ' '.join(parts[3:]) if len(parts) > 3 else None, None

DIRECT_TRANSLATION_PATTERN = re.compile(r'^([a-zA-Z]{2})\s+(.+)$')

async def translate_message(jarvis:Jarvis_client, message, chat, text, original_text=None):
    """Основная функция перевода"""
    # Проверяем новый формат команды
    direct_match = DIRECT_TRANSLATION_PATTERN.match(text)
    if direct_match:
        target_lang = direct_match.group(1).lower()
        text_to_translate = direct_match.group(2)
        
        # Проверяем поддержку языка
        if target_lang not in LANGUAGES.values():
            return "Язык не поддерживается"
            
        try:
            translated = ts.translate_text(
                text_to_translate,
                translator='yandex',
                from_language='auto',
                to_language=target_lang
            )
            return await jarvis.client.edit_message(chat, message.id, translated)
        except Exception as e:
            return f"Ошибка перевода: {str(e)}"
        
    # Если команда без параметров - берем текст из предыдущего сообщения
    elif text.strip() == 'переведи':
        async for msg in jarvis.client.iter_messages(
            chat, limit=2, reverse=True
        ):
            if msg.id != message.id:
                text_to_translate = msg.text
                break
        else:
            return "Не найдено сообщение для перевода"
        
        # Автоматически определяем язык перевода
        target_lang = 'en' if is_russian_word(text_to_translate.split()[0]) else 'ru'
    else:
        # Парсим команду
        target_lang, text_to_translate, error = parse_translation_command(text)
        if error:
            return f"Ошибка: {error}"
        
        # Если текст не указан - берем из reply
        if not text_to_translate and message.is_reply:
            reply_msg = await message.get_reply_message()
            text_to_translate = reply_msg.text
    
    # Проверяем язык перевода
    if target_lang not in LANGUAGES.values():
        return "Язык не поддерживается"
    
    try:
        # Выполняем перевод с указанием исходного языка
        translated = ts.translate_text(
            text_to_translate,
            translator='yandex',
            from_language='auto',
            to_language=target_lang
        )
        return f"Перевод на {get_language_name(target_lang)}:\n{translated}"
    except Exception as e:
        return f"Ошибка перевода: {str(e)}"

def get_language_name(code):
    """Возвращает полное название языка по коду"""
    for lang, lang_code in LANGUAGES.items():
        if lang_code == code:
            return lang
    return "неизвестный язык"

async def start(jarvis: Jarvis_client, new_message: My_message):
    """Обработчик команды перевода"""
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"].get(PATH, False):
        return
    
    message = new_message.message
    chat = new_message.chat
    text = message.text.lower()
    
    if text.startswith('переведи') or DIRECT_TRANSLATION_PATTERN.match(text):
        translation_result = await translate_message(jarvis, message, chat, text)
        if type(translation_result) is str:
            await jarvis.send_message(message, translation_result)
        return True