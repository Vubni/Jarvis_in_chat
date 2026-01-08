from json import load, dumps
from aiogram import Router, F
from aiogram.types import Message

import keyboards.inline_kbs as kb
import keyboards.settings_chats as kb_chats

from database.database import Database
import config, pytz, json
from aiogram.types import ReplyKeyboardRemove as KRemove
from html import escape
from FSM import fsm
from database.functions import save_settings
from config import jarvis_all, data_users

from datetime import datetime
from dateutil.relativedelta import relativedelta

from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton
from create_bot import bot
import keyboards.settings_chats as kb_chats
from functions.functions import clean_html


router_fsm = Router()

@router_fsm.message(F.chat_shared, fsm.Attention_edit.news)
async def attention_edit_news(message: Message):
    user_id = message.from_user.id
    await fsm.delete_register(user_id)
    if message.text == "❌Отмена":
        await message.answer("Отменено!", reply_markup=kb.back("attention"))
        await (await message.answer("Удаление кнопки. . .", reply_markup=KRemove())).delete()
        return
    if not message.chat_shared:
        return
    jarvis_all[data_users[message.chat.id]].settings["news_channel"] = message.chat_shared.chat_id

    await save_settings(user_id)
    await (await message.answer("Удаление кнопки. . .", reply_markup=KRemove())).delete()
    await message.answer("Успешно!", reply_markup=kb.back("attention"))

@router_fsm.message(F.text, fsm.Attention_edit.weat)
async def attention_edit_weat(message: Message):
    user_id = message.from_user.id
    await fsm.delete_register(user_id)
    if message.text == "❌Отмена":
        await message.answer("Отменено!", reply_markup=kb.back("attention"))
        return
    jarvis_all[data_users[message.chat.id]].settings["attention"]["weather"]["city"] = message.text

    await save_settings(user_id)
    await message.answer("Успешно!", reply_markup=kb.back("attention"))

@router_fsm.message(F.text, fsm.Oplata.promo)
async def promo_use(message: Message):
    user_id = message.from_user.id
    async with Database() as db:
        res = await db.execute("SELECT * FROM promo_codes WHERE code=$1", (message.text,))
        if not res:
            return await message.answer("<b>❌Промокод не найден!❌</b> Попробуйте ещё раз!", reply_markup=kb.back("profile"))
        today = datetime.now()
        if res["limit_day"] < today.date():
            await db.execute(("DELETE FROM promo_codes WHERE code=$1", (message.text,)))
            return await message.answer("<b>❌Срок действия промокода вышел❌</b> Попробуйте другой промокод!", reply_markup=kb.back("profile"))
    if res["type"] != "СКИДКА":
        await fsm.delete_register(user_id)
        async with Database() as db:
            await db.execute("UPDATE promo_codes SET count=count-1 WHERE code=$1", (message.text,))
            await db.execute("DELETE FROM promo_codes WHERE count <= 0")
            if not jarvis_all[data_users[user_id]].subscription:
                subscription = {"charge_id": "", "type": res["type"],
                            "date_subscription": (today).strftime("%Y-%m-%d"), 
                            "paid_before": (today + relativedelta(days=res["bonus"])).strftime("%Y-%m-%d"), 
                            "by_price": 0, 
                            "is_stock": True}
                await db.execute("UPDATE profiles SET subscription=$1 WHERE user_id=$2", (json.dumps(subscription), user_id))
                await db.close_connection()
                await jarvis_all[data_users[message.chat.id]].update_subscription()
                version, bonus = res["type"], res["bonus"]
                return await message.answer(f"<b>Успешно выдана версия {version}, на {bonus} дней!🔥</b>")
            
            subscription = (await db.execute("SELECT subscription FROM profiles WHERE user_id=$1", (user_id,)))["subscription"]
            subscription["paid_before"] = (datetime.strptime(subscription["paid_before"], "%Y-%m-%d") + relativedelta(days=res["bonus"])).strftime("%Y-%m-%d")
            if subscription["subscription"] and subscription["subscription"]["status"]:
                await bot.edit_user_star_subscription(user_id, subscription["charge_id"], True)
                subscription["subscription"] = False
            subscription["by_price"] = 0
            await db.execute("UPDATE profiles SET subscription=$1 WHERE user_id=$2", (json.dumps(subscription), user_id))
            await db.close_connection()
            await jarvis_all[data_users[message.chat.id]].update_subscription()
            version, bonus = res["type"], res["bonus"]
            return await message.answer(f"<b>Успешно выдана версия {version}, на {bonus} дней!🔥</b>")
        
    await fsm.set_data({"promo_code" : message.text}, user_id)
    bonus = res["bonus"]
    await message.answer(f"<b>В случае оплаты - будет применён промокод на скидку {bonus}%🔥</b>")
    async with Database() as db:
        prices = await db.execute_all("SELECT DISTINCT type FROM prices")
        bonus = 0
        inline_kb_list = []
        data = await fsm.get_data(user_id)
        if "promo_code" in data:
            bonus = (await db.execute("SELECT bonus FROM promo_codes WHERE code=$1", (data["promo_code"],)))["bonus"] / 100
        for row in prices:
            type_price = row["type"]
            price_month = (await db.execute("SELECT price_month FROM prices WHERE price_month = (SELECT MIN(price_month) FROM prices WHERE type=$1) and type=$1", (row["type"],)))["price_month"]
            inline_kb_list.append([IButton(text=type_price + f" (От {int(price_month - (price_month * bonus))}⭐/месяц)", callback_data=f'oplata|{type_price}')])
    inline_kb = IMarkup(inline_keyboard=inline_kb_list)
    await message.answer("<b>Выбери интересующую вас подписку:</b>", reply_markup=inline_kb)
    await fsm.register_next(fsm.Oplata.version, user_id)


@router_fsm.message(F.text, fsm.Bot_off.reason)
async def reason_bot_off(message: Message):
    user_id = message.from_user.id
    await fsm.delete_register(user_id)
    async with Database() as db:
        await db.execute("UPDATE profiles SET reason=$1 WHERE user_id=$2", (message.text, user_id))
    await message.answer("<b>Большое спасибо за указание причины!</b>\nЯ учту это и исправлюсь в ближайших обновлениях💓\n\n<italic>P.S. На всякий случай я оставлю для вас кнопочку😁</italic>",
                         reply_markup=kb.connect_again())
    

@router_fsm.message(F.text, fsm.Ping_check.check)
async def correct_connect(message: Message):
    user_id = message.from_user.id
    if "понг" not in message.text.lower():
        if "пинг" != message.text.lower():
            await message.answer("Я ожидаю сообщение '<b>пинг</b>', чтобы показать, что я могу!")
        else:
            if not (await jarvis_all[data_users[user_id]].check_connect()):
                await jarvis_all[data_users[user_id]].stop_func()
                await message.answer("К сожалению, соединение с ботом было прервано по какой-то причине.\n<b>Пожалуйста, пройдите подключение повторно!</b>", reply_markup=kb.connect_again())
                await fsm.delete_register(user_id)
        return
    await fsm.delete_register(user_id)
    msg = await message.answer("""Как видишь, я успешно подключён!❤️‍🔥 Теперь ты можешь более подобно ознакомиться с моим функционалом:


<b>🗑️Имитация удаления сообщения</b> - то, что я напишу, если замечу, что кто-то удалил сообщение!

<b>✏️Имитация изменения сообщения</b> - то, что я напишу, если замечу, что кто-то изменил сообщение!

<b>📜Список команд</b> - мой список команд

<b>🛠️Основное меню настроек (/start)</b> - настройки и список команд!""", reply_markup=kb.pin_message())
    await msg.pin()


@router_fsm.message(F.text, fsm.Answer_create.text_from_set)
async def create_answer_finally(message: Message):
    user_id = message.from_user.id
    await fsm.set_data({"text_from": message.text}, user_id)
    await message.answer("_*Шаг 2*_\.\nВыберите тип автоматического ответа:", reply_markup=kb.create_answer_type_all())


@router_fsm.message(F.text, fsm.Answer_create.answer_set)
async def create_answer_finally(message: Message):
    user_id = message.from_user.id
    data = await fsm.get_data(user_id)
    await fsm.delete_register(user_id)
    markup = []
    async with Database() as db:
        await db.execute("INSERT INTO auto_answering (user_id, text_from, text_to, type) VALUES ($1, $2, $3, $4)", (user_id, data["text_from"], message.text, data["type"]))
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
    markup.append([IButton(text='«', callback_data='settings')])
    await message.answer(f"Здесь вы можете создать <b>до 100</b> автоматических ответов в подписках Джарвис и <b>до {config.LIMIT_AUTO_ANSWERS}</b> в бесплатном боте.", reply_markup=IMarkup(inline_keyboard=markup))
    
@router_fsm.message(F.text, fsm.Prefix.edit)
async def create_answer_finally(message: Message):
    user_id = message.from_user.id
    jarvis_all[data_users[user_id]].settings["prefix"]["text"] = clean_html(message.text)
    await save_settings(user_id)
    await fsm.delete_register(user_id)
    await message.answer("🟢Префикс успешно изменён!")
    prefix = message.text + ":"
    await message.answer(f"""🎭 <b>О нет, вы тоже из этих?</b>  
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
    
    
@router_fsm.message(F.user_shared | F.chat_shared, fsm.Antispam._except)
async def create_antispam_except(message: Message):
    user_id = message.from_user.id
    if message.user_shared:
        id_obj = message.user_shared.user_id
    elif message.chat_shared:
        id_obj = message.chat_shared.chat_id
    else:
        return
    jarvis_all[data_users[user_id]].settings["antispam"]["except"].append(id_obj)
    await save_settings(user_id)
    await message.answer("""<b>🌟 Настройка антиспам-бота</b>
Добро пожаловать в <i>интеллектуальный антиспам</i>! Чтобы защитить ваш чат от нежелательных сообщений, используйте следующие возможности:

<u>Основные функции:</u>
• <b>Автоматическая блокировка</b> флуда и спама
• <code>/report</code> — мгновенная жалоба на сообщение/пользователя
• <a href="https://vubni.gitbook.io/jarvis/besplatnaya-versiya/unikalnye-vozmozhnosti/antispam">Инструкция</a> по настройке

<u>⚠️ Важно:</u>
Вы можете <s>добавить до 10 чатов</s> в <b>исключения</b>, где антиспам будет отключен.""", reply_markup=await kb.antispam_except(user_id))
    
@router_fsm.message(F.user_shared | F.chat_shared, fsm.Chats_settings.chats_except)
async def create_chat_except(message: Message):
    user_id = message.from_user.id
    if message.user_shared:
        id_obj = message.user_shared.user_id
    elif message.chat_shared:
        id_obj = message.chat_shared.chat_id
    else:
        return
    indx = 0
    for item in jarvis_all[data_users[user_id]].settings["func_except"]:
        if item["id"] == id_obj:
            name = await jarvis_all[data_users[user_id]].get_title_or_name(id_obj)
            return await message.answer(f"Настройки для доступа Джарвис к чату {name}", reply_markup=kb_chats.settings_except(indx, user_id))
        indx += 1
    jarvis_all[data_users[user_id]].settings["func_except"].append({"id": id_obj, "edit": False, "del": False, "command": False})
    await save_settings(user_id)
    name = await jarvis_all[data_users[user_id]].get_title_or_name(id_obj)
    id_ = len(jarvis_all[data_users[user_id]].settings["func_except"]) - 1
    await message.answer(f"Настройки для доступа Джарвис к чату {name}", reply_markup=kb_chats.settings_except(id_, user_id))