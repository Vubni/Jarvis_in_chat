import re
from config import jarvis_all, data_users
from modules.correcting_layout.settings import PATH
from TelegramClient import Jarvis_client
from functions.functions import My_message

status = True

def replace_english_to_opposite_russian(text):
    layout = {
        ord('q'): 'й', ord('w'): 'ц', ord('e'): 'у', ord('r'): 'к',
        ord('t'): 'е', ord('y'): 'н', ord('u'): 'г', ord('i'): 'ш',
        ord('o'): 'щ', ord('p'): 'з', ord('['): 'х', ord(']'): 'ъ',
        ord('a'): 'ф', ord('s'): 'ы', ord('d'): 'в', ord('f'): 'а',
        ord('g'): 'п', ord('h'): 'р', ord('j'): 'о', ord('k'): 'л',
        ord('l'): 'д', ord(';'): 'ж', ord("'"): 'э', ord('z'): 'я',
        ord('x'): 'ч', ord('c'): 'с', ord('v'): 'м', ord('b'): 'и',
        ord('n'): 'т', ord('m'): 'ь', ord(','): 'б', ord('.'): 'ю',
        ord('/'): '.', ord('`'): 'ё', ord('&'): '?',
        ord('Q'): 'Й', ord('W'): 'Ц', ord('E'): 'У', ord('R'): 'К',
        ord('T'): 'Е', ord('Y'): 'Н', ord('U'): 'Г', ord('I'): 'Ш',
        ord('O'): 'Щ', ord('P'): 'З', ord('{'): 'Х', ord('}'): 'Ъ',
        ord('A'): 'Ф', ord('S'): 'Ы', ord('D'): 'В', ord('F'): 'А',
        ord('G'): 'П', ord('H'): 'Р', ord('J'): 'О', ord('K'): 'Л',
        ord('L'): 'Д', ord(':'): 'Ж', ord('"'): 'Э', ord('Z'): 'Я',
        ord('X'): 'Ч', ord('C'): 'С', ord('V'): 'М', ord('B'): 'И',
        ord('N'): 'Т', ord('M'): 'Ь', ord('<'): 'Б', ord('>'): 'Ю',
        ord('?'): ',', ord('~'): 'Ё', ord('|'): '/', ord('^'): ':',
        ord('@'): '"', ord('#'): '№'
    }
    return text.translate(layout)

def replace_russian_to_opposite_english(text):
    layout = {
        ord('й'): 'q', ord('ц'): 'w', ord('у'): 'e', ord('к'): 'r',
        ord('е'): 't', ord('н'): 'y', ord('г'): 'u', ord('ш'): 'i',
        ord('щ'): 'o', ord('з'): 'p', ord('х'): '[', ord('ъ'): ']',
        ord('ф'): 'a', ord('ы'): 's', ord('в'): 'd', ord('а'): 'f',
        ord('п'): 'g', ord('р'): 'h', ord('о'): 'j', ord('л'): 'k',
        ord('д'): 'l', ord('ж'): ';', ord('э'): "'", ord('я'): 'z',
        ord('ч'): 'x', ord('с'): 'c', ord('м'): 'v', ord('и'): 'b',
        ord('т'): 'n', ord('ь'): 'm', ord('б'): ',', ord('ю'): '.',
        ord('.'): '/', ord('ё'): '`', ord('?'): '&',
        ord('Й'): 'Q', ord('Ц'): 'W', ord('У'): 'E', ord('К'): 'R',
        ord('Е'): 'T', ord('Н'): 'Y', ord('Г'): 'U', ord('Ш'): 'I',
        ord('Щ'): 'O', ord('З'): 'P', ord('Х'): '{', ord('Ъ'): '}',
        ord('Ф'): 'A', ord('Ы'): 'S', ord('В'): 'D', ord('А'): 'F',
        ord('П'): 'G', ord('Р'): 'H', ord('О'): 'J', ord('Л'): 'K',
        ord('Д'): 'L', ord('Ж'): ':', ord('Э'): '"', ord('Я'): 'Z',
        ord('Ч'): 'X', ord('С'): 'C', ord('М'): 'V', ord('И'): 'B',
        ord('Т'): 'N', ord('Ь'): 'M', ord('Б'): '<', ord('Ю'): '>',
        ord(','): '?', ord('Ё'): '~', ord('/'): '|', ord(':'): '^',
        ord('"'): '@', ord('№'): '#', ord(';'): '$'
    }
    return text.translate(layout)

def contains_english_letters(text):
    return bool(re.search('[a-zA-Z]', text))

def contains_russian_letters(text):
    return bool(re.search(r'[а-яА-ЯёЁ]', text))

async def start(jarvis: Jarvis_client, new_message: My_message):
    if not jarvis_all[data_users[jarvis.user.id]].settings["modules"][PATH]:
        return
    
    message = new_message.message
    text = message.message.lower()
    reply_message = new_message.reply_message
    
    if ".исправь" == text or ".cl" == text or ".испр" == text:
        if reply_message and reply_message.message:
            text = reply_message.message.lower()
        else:
            async for reply_message in jarvis.client.iter_messages(new_message.chat, limit=2):
                if reply_message.id == message.id:
                    continue
                text = reply_message.message
                break
        new_text= ""
        for word in text.split(" "):
            if contains_english_letters(word):
                new_text += replace_english_to_opposite_russian(word)+ " "
            elif contains_russian_letters(word):
                new_text += replace_russian_to_opposite_english(word) + " "
        await message.delete()
        return await reply_message.edit(text=new_text)