from json import load, dumps
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message

import keyboards.inline_kbs as kb
import keyboards.reply_kbs as rp_kb

import functions.reg as func_reg
from database.database import Database
from database.functions import save_settings
import config
from aiogram.types import ReplyKeyboardRemove as KRemove
from aiogram.types import CallbackQuery
from FSM import fsm

from aiogram.types import InlineKeyboardButton as IButton
from aiogram.types import InlineKeyboardMarkup as IMarkup

from clients_run import start_client

from config import data_users, jarvis_all
import s3

router_call_settings = Router()

@router_call_settings.callback_query(F.data == 'currency')
async def currency(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await message.edit_text("Здесь вы можете выбрать настроить команду курса валют.\n\n<a href='https://vubni.gitbook.io/jarvis/besplatnaya-versiya/obychnye-komandy/kurs-valyut'>Подробнее про команду</a>", 
                            reply_markup=kb.settings_currency(user_id))
    
@router_call_settings.callback_query(F.data.startswith('currency|'))
async def currency_edit(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    data = call.data.replace("currency|", "")
    temp = {"off": False, "on": True}
    jarvis_all[data_users[user_id]].settings["currency"] = temp[data]
    await save_settings(user_id)
    await message.edit_text("Здесь вы можете выбрать настроить команду курса валют.\n\n<a href='https://vubni.gitbook.io/jarvis/besplatnaya-versiya/obychnye-komandy/kurs-valyut'>Подробнее про команду</a>", 
                            reply_markup=kb.settings_currency(user_id))
    
@router_call_settings.callback_query(F.data.startswith('attention'))
async def attention(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await fsm.delete_register(user_id)
    text = "📣Сообщения внимания - уведомления, присылаемые утром и вечером с пожеланиями и важной информацией, а также по праздникам!"
    if "save_post" in call.data:
        return await message.answer(text, reply_markup=kb.settings_attention(user_id))
    await message.edit_text(text, reply_markup=kb.settings_attention(user_id))

@router_call_settings.callback_query(F.data.startswith('atten|edit'))
async def attention_edit(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    data = call.data
    if "news" in data:
        await message.delete()
        await message.answer("Нажмите '🌐Отправить канал' и отправьте канал, который хотели бы отслеживать для ежедневных рандомных новостей!", reply_markup=rp_kb.attention_edit_news())
        await fsm.register_next(fsm.Attention_edit.news, user_id)
    elif "weat" in data:
        await message.edit_text("Отправьте название города/посёлка, погоду которого хотели бы получать в ежедневной информации!", reply_markup=kb.back("attention"))
        await fsm.register_next(fsm.Attention_edit.weat, user_id)

@router_call_settings.callback_query(F.data.startswith('atten|'))
async def atten(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    data = call.data
    if "|all|" in data:
        if "on" in data:
            jarvis_all[data_users[user_id]].settings["attention"]["status"] = True
        else:
            jarvis_all[data_users[user_id]].settings["attention"]["status"] = False
    elif "|news|" in data:
        if "on" in data:
            jarvis_all[data_users[user_id]].settings["attention"]["news"] = True
        else:
            jarvis_all[data_users[user_id]].settings["attention"]["news"] = False
    elif "|weat|" in data:
        if "on" in data:
            jarvis_all[data_users[user_id]].settings["attention"]["weather"]["status"] = True
        else:
            jarvis_all[data_users[user_id]].settings["attention"]["weather"]["status"] = False
    elif "|curren|" in data:
        if "on" in data:
            jarvis_all[data_users[user_id]].settings["attention"]["currency"] = True
        else:
            jarvis_all[data_users[user_id]].settings["attention"]["currency"] = False
            
    await save_settings(user_id)
    await message.edit_text("📣Сообщения внимания - уведомления, присылаемые утром и вечером с пожеланиями и важной информацией, а также по праздникам!", reply_markup=kb.settings_attention(user_id))

@router_call_settings.callback_query(F.data == 'smart_home')
async def smart_home(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    async with Database() as db:
        res = await db.execute("SELECT * FROM smart_home WHERE user_id=$1", (user_id,))
        if res:
            return await message.edit_text("Здесь в будущем появятся настройки умного дома! В данный момент можно отвязать яндекс аккаунт.", reply_markup=kb.settings_smarthome())
    await message.edit_text("Для управления умным домом Яндекс - требуется подключить аккаунт с привязанным умным домом!", reply_markup=kb.create_smarthome())
    await message.answer("Кнопка для подключения создана!", reply_markup=rp_kb.yandex_connect())

    
@router_call_settings.callback_query(F.data.startswith('smart|'))
async def smart_home_settings(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    async with Database() as db:
        await db.execute("DELETE FROM smart_home WHERE user_id=$1", (user_id,))
    jarvis_all[data_users[user_id]].yandex_token = None
    await call.answer("Аккаунт успешно отвязан!")
    await message.edit_text("Для управления умным домом Яндекс - требуется подключить аккаунт с привязанным умным домом!", reply_markup=kb.create_smarthome())
    await message.answer("Кнопка для подключения создана!", reply_markup=rp_kb.yandex_connect())

@router_call_settings.callback_query(F.data == 'quick_answers')
async def quick_answers(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await fsm.delete_register(user_id)
    subscription = jarvis_all[data_users[call.from_user.id]].subscription
    async with Database() as db:
        result = await db.execute_all("SELECT id, phrase FROM quick_answers WHERE user_id=$1", (user_id,))
    if not subscription:
        return await message.edit_text(f"Здесь вы можете создать <b>до {config.LIMIT_QUICK_ANSWERS}</b> быстрых ответов или <b>любое количество</b> ответов, перейдя на любую <a href='{config.SUBSCRIPTION_URL}'>подписку</a>!", reply_markup=kb.quick_answers(result, subscription))
    await message.edit_text(f"Здесь вы можете создать <b>любое количество</b> быстрых ответов!", reply_markup=kb.quick_answers(result, subscription))

@router_call_settings.callback_query(F.data == 'create|quick')
async def create_quick(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await fsm.register_next(fsm.Quick_answer.create, user_id)
    await message.edit_text(f"<b><i>Шаг 1</b></i>.\nОтправьте фразу, на которую будет реагировать быстрый ответ!", reply_markup=kb.back("quick_answers"))

@router_call_settings.callback_query(F.data.startswith('quick|del|'))
async def quick_delete(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    id_quick = call.data.replace("quick|del|", "")
    subscription = jarvis_all[data_users[call.from_user.id]].subscription
    async with Database() as db:
        await db.execute("DELETE FROM quick_answers WHERE id=$1", (id_quick,))
        result = await db.execute_all("SELECT id, phrase FROM quick_answers WHERE user_id=$1", (user_id,))
    await call.answer("Успешно удалено!")
    if not subscription:
        return await message.edit_text(f"Здесь вы можете создать <b>до {config.LIMIT_QUICK_ANSWERS}</b> быстрых ответов или <b>любое количество</b> ответов, перейдя на любую <a href='{config.SUBSCRIPTION_URL}'>подписку<a>!", reply_markup=kb.quick_answers(result, subscription))
    await message.edit_text(f"Здесь вы можете создать <b>любое количество</b> быстрых ответов!", reply_markup=kb.quick_answers(result, subscription))

@router_call_settings.callback_query(F.data.startswith('quick|'))
async def quick_info(call: CallbackQuery):
    message = call.message
    id_quick = call.data.replace("quick|", "")
    subscription = jarvis_all[data_users[call.from_user.id]].subscription
    async with Database() as db:
        result = await db.execute("SELECT * FROM quick_answers WHERE id=$1", (id_quick,))
        await message.edit_text(f"""Информация о автоматическом ответе №{id_quick}:

<b>Фраза реагирования:</b> <code>{result[2]}</code>
<b>Ответ/настройка jarvis ai:</b> <code>{result[3]}</code>""", reply_markup=kb.quick_answer(id_quick, subscription))
        
@router_call_settings.callback_query(F.data == 'browser_settings')
async def browser_settings(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await message.edit_text("Здесь вы можете выбрать браузер, который будет открываться по умолчанию по команде <b>'Браузер'</b>", reply_markup=kb.browser_settings(user_id))

@router_call_settings.callback_query(F.data.startswith('browser|'))
async def browser_edit(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    idx_new = int(call.data.replace("browser|", ""))
    if idx_new == -1:
        return await call.answer("Текущий браузер, который будет открываться", True)
    jarvis_all[data_users[user_id]].settings["browser"] = idx_new
    await save_settings(user_id)
    await message.edit_text("Здесь вы можете выбрать браузер, который будет открываться по умолчанию по команде <b>'Браузер'</b>", reply_markup=kb.browser_settings(user_id))


@router_call_settings.callback_query(F.data == 'antispam')
async def antispam(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    if jarvis_all[data_users[user_id]].subscription:
        await fsm.delete_register(user_id)
        await (await message.answer("Удаление кнопки...", reply_markup=KRemove())).delete()
    await message.edit_text("Настройки антиспама. Здесь вы можете включить или выключить антиспам, настроить его или добавить исключения!", reply_markup=kb.antispam_settings(user_id))

@router_call_settings.callback_query(F.data.startswith('anti|exc'))
async def antispam_settings(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    data = call.data.replace("anti|exc", "")
    if data:
        data = int(data.replace("|", ""))
        jarvis_all[data_users[user_id]].settings["antispam"]["except"].pop(data)
        await save_settings(user_id)
    else:
        await message.answer("Создание кнопки . . .", reply_markup=kb.new_except_antispam(user_id))
        await fsm.register_next(fsm.Antispam._except, user_id)
    await message.edit_text("""<b>🌟 Настройка антиспам-бота</b>
Добро пожаловать в <i>интеллектуальный антиспам</i>! Чтобы защитить ваш чат от нежелательных сообщений, используйте следующие возможности:

<u>Основные функции:</u>
• <b>Автоматическая блокировка</b> флуда и спама
• <code>/report</code> — мгновенная жалоба на сообщение/пользователя
• <a href="https://vubni.gitbook.io/jarvis/besplatnaya-versiya/unikalnye-vozmozhnosti/antispam">Инструкция</a> по настройке

<u>⚠️Важно:</u>
Вы можете добавить любое количество чатов в <b>исключения</b>, где антиспам будет отключен.""", reply_markup=await kb.antispam_except(user_id))

@router_call_settings.callback_query(F.data.startswith('anti|sens'))
async def antispam_settings(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    data = call.data.replace("anti|sens", "")
    if data:
        data = int(data.replace("|", "")) + 1
        if jarvis_all[data_users[user_id]].settings["antispam"]["sensitivity"] == data:
            return await call.answer("Данная настройка уже установлена")
        jarvis_all[data_users[user_id]].settings["antispam"]["sensitivity"] = data
        await save_settings(user_id)

    await message.edit_text("""<b>🛠️ Настройка антиспама 🛡️</b>

Выберите режим:

✅ <b>Режим "Агрессивный"</b> — бот будет жёстче блокировать подозрительные сообщения
✅ <b>Режим "Рыцарь"</b> — бот будет стараться придерживаться золотой середины, но даже рыцари ошибаются
✅ <b>Режим "Щадящий"</b> — меньше ложных срабатываний, больше свободы для ваших контактов

⚠️ <i>Внимание: Слишком строгая настройка может удалять обычные сообщения!</i>

Совет: Начните с щадящего режима 🔍, затем ужесточайте при необходимости 🔥""", reply_markup=kb.antispam_sensity(user_id))

@router_call_settings.callback_query(F.data.startswith('anti|'))
async def antispam_settings(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    if "off_ch" in call.data:
        jarvis_all[data_users[user_id]].settings["antispam"]["status_chats"] = False
    elif "on_ch" in call.data:
        jarvis_all[data_users[user_id]].settings["antispam"]["status_chats"] = True
    elif "off_gr" in call.data:
        jarvis_all[data_users[user_id]].settings["antispam"]["status_groups"] = False
    elif "on_gr" in call.data:
        jarvis_all[data_users[user_id]].settings["antispam"]["status_groups"] = True
    await save_settings(user_id)
    await message.edit_text("Настройки антиспама. Здесь вы можете включить или выключить антиспам, настроить его или добавить исключения!", reply_markup=kb.antispam_settings(user_id))


@router_call_settings.callback_query(F.data == 'main_settings')
async def main_settings(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    async with Database() as db:
        status = await db.execute("SELECT status FROM profiles WHERE user_id=$1", (user_id,))
    await message.edit_text(config.TEXT_SETTINGS,
                            reply_markup=kb.main_settings(status["status"], user_id))

@router_call_settings.callback_query(F.data.endswith('_bot'))
async def settings_bot(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    data = call.data.replace("_bot", "")
    temp = {"off": False, "on": True}
    async with Database() as db:
        await db.execute("UPDATE profiles SET status=$1 WHERE user_id=$2", (temp[data], user_id))
        phone = await db.execute("SELECT phone FROM profiles WHERE user_id=$1", (user_id,))
    if data == "off":
        await jarvis_all[data_users[user_id]].only_stop()
    else:
        await start_client(phone["phone"])
    await message.edit_text(config.TEXT_SETTINGS,
                            reply_markup=kb.main_settings(temp[data], user_id))
    
@router_call_settings.callback_query(F.data.startswith('advert_'))
async def advert_(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    data = call.data.replace("advert_", "")
    async with Database() as db:
        if data == "off":
            jarvis_all[data_users[user_id]].settings["advertisement"] = False
        else:
            jarvis_all[data_users[user_id]].settings["advertisement"] = True
        await save_settings(user_id)
    async with Database() as db:
        status = await db.execute("SELECT status FROM profiles WHERE user_id=$1", (user_id,))
    await message.edit_text(config.TEXT_SETTINGS,
                            reply_markup=kb.main_settings(status["status"], user_id))
    
@router_call_settings.callback_query(F.data == 'edit_prefix')
async def edit_prefix(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await fsm.delete_register(user_id)
    prefix = jarvis_all[data_users[user_id]].settings["prefix"]["text"] + ":" if jarvis_all[data_users[user_id]].settings["prefix"]["status"] else ""
    await message.edit_text(f"""🎭 <b>О нет, вы тоже из этих?</b>  
Тех, кто хочет переименовать вашего верного Джарвиса? Ладно-ладно... 🙄

📺Вот так я могу ответить вам сейчас:
<blockquote><b>{prefix}</b> .. .... ...</blockquote>

🔤 <u>Смена имени:</u>  
Просто нажмите кнопки ниже и превратите меня в:  
• <i>Сэр Джарвис IV</i> 🦁  
• <i>Базилио</i> 🐈
• <i>Любое ваше название</i>
<i>Или отключите префикс совсем</i>""",
                            reply_markup=kb.edit_prefix(user_id))
    
@router_call_settings.callback_query(F.data.startswith('prefix_'))
async def edit_prefix_set(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    data = call.data.replace("prefix_", "")
    if data == "edit":
        await fsm.register_next(fsm.Prefix.edit, user_id)
        return await message.edit_text("Отправь новый желаемый префикс", reply_markup=kb.back("edit_prefix"))
    if data == "off":
        jarvis_all[data_users[user_id]].settings["prefix"]["status"] = False
    elif data == "on":
        jarvis_all[data_users[user_id]].settings["prefix"]["status"]  = True
    elif data == "jarvis":
        jarvis_all[data_users[user_id]].settings["prefix"]["text"] = "Джарвис"
    await edit_prefix(call)
    
    
@router_call_settings.callback_query(F.data == 'answering')
async def answering(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await fsm.delete_register(user_id)
    markup = []
    subscription = jarvis_all[data_users[call.from_user.id]].subscription
    async with Database() as db:
        results = await db.execute_all("SELECT * FROM auto_answering WHERE user_id=$1", (user_id,))
        row = []
        indx = 1
        for item in results:
            row.append(IButton(text=item["text_from"], callback_data=f'answ|{item["id"]}'))
            if indx % 2 == 0:
                markup.append(row)
                row = []
            indx += 1
        if row:
            markup.append(row)
    if len(results) < config.LIMIT_AUTO_ANSWERS:
        markup.append([IButton(text='Создать автоматический ответ', callback_data='create_answer')])
    elif subscription:
        markup.append([IButton(text='Создать автоматический ответ', callback_data='create_answer')])
    markup.append([IButton(text='«', callback_data='modules')])
    if not subscription:
        return await message.edit_text(f"Здесь вы можете создать <b>до {config.LIMIT_AUTO_ANSWERS}</b> автоматических ответов или <b>любое количество</b> ответов, перейдя на любую <a href='{config.SUBSCRIPTION_URL}'>подписку</a>!", reply_markup=IMarkup(inline_keyboard=markup))
    await message.edit_text(f"Здесь вы можете создать <b>любое количество</b> автоматических ответов!", reply_markup=IMarkup(inline_keyboard=markup))
    

@router_call_settings.callback_query(F.data.startswith('cloud|'))
async def delete_cloud(call: CallbackQuery):
    cloud_id = int(call.data.replace("cloud|", ""))
    async with Database() as db:
        res = await db.execute("SELECT user_id, content FROM saved_messages WHERE id=$1", (cloud_id,))
        if not res:
            return call.answer("Сообщение уже удалено из облака!")
        if res["user_id"] != call.from_user.id:
            return call.answer("Сообщение сохранено не в вашем облаке!")
        if res["content"]:
            s3_key = res["content"].split("=")[1]
            await s3.delete_object("cloud/" + s3_key)
        await db.execute("DELETE FROM saved_messages WHERE id=$1", (cloud_id,))
    await call.answer("Успешно удалёно!")

@router_call_settings.callback_query(F.data == 'create_answer')
async def create_answer(call: CallbackQuery):
    message = call.message
    await message.edit_text("Выберите тип ответа.\n\nОтвет на первое сообщение будет отвечать только если человек пишет первый раз, обычный ответ - когда угодно!", reply_markup=kb.create_answer())

@router_call_settings.callback_query(F.data.startswith('create_answer_'))
async def create_answer_2(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    type_answer = int(call.data[-1])
    if type_answer == 1:
        await fsm.register_next(fsm.Answer_create.text_from_set, user_id)
        await message.edit_text("<b>Шаг 1</b>.\nОтправьте фразу, на которую будет реагировать автоматический ответ!", reply_markup=kb.back("answering"))
    elif type_answer == 2:
        await fsm.set_data({"text_from": "one_message"}, user_id)
        await message.edit_text("<b>Шаг 2</b>.\nВыберите тип автоматического ответа:", reply_markup=kb.create_answer_type_2())

@router_call_settings.callback_query(F.data.startswith('answer_type_'))
async def create_answer_2(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    type_answer = int(call.data[-1])
    await fsm.set_data({"type": type_answer}, user_id)
    await fsm.register_next(fsm.Answer_create.answer_set, user_id)
    if type_answer != 4:
        await message.edit_text("<b>Шаг 3</b>.\nНапишите фразу, которой я буду отвечать в этом случае.", reply_markup=kb.back("answering"))

@router_call_settings.callback_query(F.data.startswith('answ_del_'))
async def answering_edit(call: CallbackQuery):
    id_answer = int(call.data.replace("answ_del_", ""))
    async with Database() as db:
        await db.execute("DELETE FROM auto_answering WHERE id=$1", (id_answer,))
    await call.answer("Успешно удалено✅")
    await answering(call)


@router_call_settings.callback_query(F.data.startswith('answ|'))
async def answering_edit(call: CallbackQuery):
    message = call.message
    id_answer = int(call.data.replace("answ|", ""))
    async with Database() as db:
        result = await db.execute("SELECT * FROM auto_answering WHERE id=$1", (id_answer,))
    answer_type = ["Обычный ответ", "Ответ, если не в сети", "Ответ, если в сети", "Ответ от Jarvis Ai"]
    await message.edit_text(f"""Информация о автоматическом ответе №{id_answer}:

<b>Фраза активации:</b> {result["text_from"]}
<b>Тип ответа:</b> {answer_type[result["type"] - 1]}
<b>Ответ/настройка jarvis ai:</b> {result["text_to"]}""", reply_markup=kb.answer_settings(id_answer))