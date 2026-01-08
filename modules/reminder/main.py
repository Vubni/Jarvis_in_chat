from openai import OpenAI
import ast, pytz
import pymysql, asyncio
from datetime import datetime
import telebot

moscow_tz = pytz.timezone('Europe/Moscow')

status = False


token = "6656913989:AAG3A1dgtiIUVFVf2cI_-Kus0D4jv7jz35M"
API_TOKEN = token
bot = telebot.TeleBot(API_TOKEN)


class Reminder():
    def __init__(self) -> None:
        self.name = "напоминания"
        self.phrases = self.find_call
        self.jarvis = None
        self.async_func = self.call_reminder
        self.await_action = []
        self.await_action_phrases = []

        self.await_message = []

        self.ollama = OpenAI(
            base_url='http://localhost:11434/v1',
            api_key='ollama',
        )

    async def find_call(self, message):
        text = message.text.lower()
        phrases = ['напомни ', ' напомни', "создай напоминание", "завтра", "напоминай", "через час", "через пол часа"]
        if len(text.split()) >= 2:
            if any(keyword in text for keyword in phrases) and '?' not in text:
                return await self.check_reminder(text)
        return False

    async def check_reminder(self, text):
        response = self.ollama.chat.completions.create(
            model="qwen2:1.5b",
            messages=[{
        "role": "user",
        "content": f"Прошу проанализировать следующее предложение. Ответь 1, если в предложении содержится план о котором следует поставить напоминание, 0 — если намерения нет, предложение бессмысленно или не имеет четкой цели. Пример: 'Надо сходить в магазин завтра'. А теперь анализируй следующее: '{text}'. Пожалуйста, не реагируй на обычные вопросы или простые слова, сосредоточься только на предложениях с явным планом или намерением. Также ответь 0, если в предложении идёт речь о каких-либо запрещённых вещах или о том, что может навредить жизни человека."}]
        )
        t5_output = response.choices[0].message.content
        try:
            if int(t5_output) == 1:
                return True
        except:
            return False
        return False

    async def call(self, from_user):
        return "Если хотите, я могу напомнить вам об этом!"

    async def call_reminder(self):
        connection = None
        while True:
            if connection is None or not connection.open:
                connection = pymysql.connect(
                    host='77.222.37.120',
                    user='user',
                    password='OZWQjiZy-R8piGhVU-A6L0tgMn-JARVIS',
                    database='jarvis_tg'
                )
            with connection.cursor() as cursor:
                sql = "SELECT * FROM reminders WHERE premium=0 and DATE_FORMAT(date_time, '%Y-%m-%d %H:%i') <= DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i')"
                cursor.execute(sql)
                result = cursor.fetchall()
                sql = "DELETE FROM reminders WHERE premium=0 and DATE_FORMAT(date_time, '%Y-%m-%d %H:%i') <= DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i')"
                cursor.execute(sql)
                connection.commit()
                if result:
                    for row in result:
                        try:
                            bot.send_message(row[1], f"_*Напоминаю\!*_ Вы хотели:\n`{row[2]}`", parse_mode="MarkdownV2")
                        except Exception as e:
                            print("ошибка при попытке напоминания: ", e)

            await asyncio.sleep(60)

    
    async def edit_reminder(self, message, text, date):
        self.await_action_phrases = [["заголовок", "название"], ["дату", "время", "число"]]
        self.await_action = [[self.edit_text, (date,)], [self.edit_date, (text,)]]
        await self.jarvis.client.send_message(message.chat_id, "Джарвис: Пожалуйста, напишите, *что именно вы хотели бы изменить*:\n\n`Заголовок` или `дату`?", parse_mode="Markdown")


    async def edit_text(self, message, date):
        self.await_message = [self.set_new_text, (date,)]
        await self.jarvis.client.send_message(message.chat_id, "Джарвис: Напишите новый заголовок для напоминания")

    async def set_new_text(self, message, date):
        text = message.text
        await self.jarvis.client.send_message(message.chat_id, f"Джарвис: После изменений, я могу создать следующее напоминание:\n\nЗаголовок: `{text}`\nДата: `{date}`\n\nСоздать или вы хотели бы что-либо изменить?", parse_mode="Markdown")
        self.jarvis.action[message.chat_id] = [self.save_reminder, (text, date)]
        self.jarvis.edit_action[message.chat_id] = [self.edit_reminder, (text, date)]

    async def edit_date(self, message, text):
        self.await_message = [self.set_new_date, (text,)]
        await self.jarvis.client.send_message(message.chat_id, "Джарвис: Напишите новую дату для напоминания в формате:\n`ДД.ММ.ГГГГ ЧЧ:ММ`", parse_mode="Markdown")

    async def set_new_date(self, message, text):
        date = message.text
        await self.jarvis.client.send_message(message.chat_id, f"Джарвис: После изменений, я могу создать следующее напоминание:\n\nЗаголовок: `{text}`\nДата: `{date}`\n\nСоздать или вы хотели бы что-либо изменить?", parse_mode="Markdown")
        self.jarvis.action[message.chat_id] = [self.save_reminder, (text, date)]
        self.jarvis.edit_action[message.chat_id] = [self.edit_reminder, (text, date)]

    async def save_reminder(self, message, text, date):
        connection = pymysql.connect(
            host='77.222.37.120',
            user='user',
            password='OZWQjiZy-R8piGhVU-A6L0tgMn-JARVIS',
            database='jarvis_tg'
        )
        with connection.cursor() as cursor:
            sql = "INSERT INTO reminders (user_id, text, date_time) VALUES(%s,%s,%s)"
            cursor.execute(sql, (message.from_id.user_id, text, datetime.strptime(date+":00", "%d.%m.%Y %H:%M:%S")))
            connection.commit()
            await self.jarvis.client.send_message(message.chat_id, f"Джарвис: Создано!\nЯ напомню тебе о `{text}` через [бота](https://t.me/vubni_jarvis_bot) ровно в `{date}`\n\nЧтобы я смог это сделать, **убедись, что бот запущен и может писать тебе сообщения!**", parse_mode="Markdown")
        connection.close()
        

    async def start(self, message, text):
        text = text.lower().replace("давай", "").replace("давайте", "").replace("напомни", "").replace("напомнишь", "").replace("напоминание", "")
        first_message  = await self.jarvis.client.send_message(message.chat_id, "Джарвис: Использование Jarvis Ai для обработки полученных данных. . .", parse_mode="Markdown")
        response = self.ollama.chat.completions.create(
            model="qwen2:7b",
            messages=[{
        "role": "user",
        "content": f"У меня есть программа, ожидающая [цель, дата и время] из диалога для создания напоминания. Выдели эту цель и время, перефразируй и напиши в требуемом формате: ['цель', 'дата и время']. Текущая дата и время: {datetime.now(moscow_tz).strftime('%d.%m.%Y %H:%M')}. Не пиши ничего кроме требуемого от тебя ответа. Если нет четкого указания на время, то пиши 9:00. Предложение: '{text}'"}]
        )
        t5_output = response.choices[0].message.content
        t5_output = ast.literal_eval(t5_output)
        try:
            await self.jarvis.client.delete_messages(message.chat_id, first_message.id)
        except:
            pass
        await self.jarvis.client.send_message(message.chat_id, f"Джарвис: Я автоматически обработал данные и могу создать такое напоминание:\n\nЗаголовок: `{t5_output[0]}`\nДата: `{t5_output[1]}`\n\nСоздать или вы хотели бы что-либо изменить?", parse_mode="Markdown")
        self.jarvis.action[message.chat_id] = [self.save_reminder, (t5_output[0], t5_output[1])]
        self.jarvis.edit_action[message.chat_id] = [self.edit_reminder, (t5_output[0], t5_output[1])]