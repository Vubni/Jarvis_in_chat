import re
from openai import OpenAI
from functions.functions import My_message
from TelegramClient import Jarvis_client
from telethon.tl import types
from database.database import Database

status = True

ollama = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',
)

async def start(jarvis : Jarvis_client, new_message : My_message):
    if jarvis.user.id == new_message.from_user.id:
        return await quick(jarvis, new_message)
    return await answer(jarvis, new_message)

async def answer(jarvis : Jarvis_client, new_message : My_message):
    message = new_message.message
    text = message.text.lower()
    async with Database() as db:
        result = await db.execute_all("SELECT * FROM auto_answering WHERE user_id=$1", (jarvis.user.id,))
    status = None
    for row in result:
        if row["text_from"] == "one_message":
            history = await jarvis.client.get_messages(message.chat_id, limit=2)
            if len(history) == 1:
                status = row
                break
        if re.search(r'\b' + re.escape(row["text_from"].lower()) + r'\b', text):
            status = row
            break
    if not status:
        return False
    user = await jarvis.client.get_me()
    async with jarvis.client.action(message.chat_id, types.SendMessageTypingAction()):
        if status["type"] == 1:
            return await jarvis.send_message(message.chat_id, status["text_to"])
        elif status["type"] == 2:
            if not isinstance(user.status, types.UserStatusOnline):
                return await jarvis.client.send_message(message.chat_id, status["text_to"])
            return False
        elif status["type"] == 3:
            if isinstance(user.status, types.UserStatusOnline):
                return await jarvis.client.send_message(message.chat_id, status["text_to"])
            return False
        return False
        response = ollama.chat.completions.create(
            model="qwen2:7b",
            messages=[{
        "role": "system",
        "content": status["text_to"]}, 
        {
        "role": "user",
        "content": text}]
        )
        t5_output = response.choices[0].message.content
        return await jarvis.client.send_message(message.chat_id, t5_output)

async def quick(jarvis : Jarvis_client, new_message : My_message):
    message = new_message.message
    text = message.text.lower()
    try:
        reply = None
        if message.reply_to and message.reply_to.forum_topic:
            if message.reply_to.reply_to_top_id:
                reply = message.reply_to.reply_to_top_id
            elif message.reply_to.reply_to_msg_id and not message.reply_to.reply_to_top_id:
                reply = message.reply_to.reply_to_msg_id
    except Exception as e:
        print("Ошибка при проверке не отвеченное ли сообщение: ", e)
        return
    async with Database() as db:
        result = await db.execute_all("SELECT * FROM quick_answers WHERE user_id=$1", (jarvis.user.id,))
    status = None
    for row in result:
        if row[2].lower() == text:
            status = row
            break
    if not status:
        return False
    async with jarvis.client.action(message.chat_id, types.SendMessageTypingAction()):
        await jarvis.client.send_message(message.chat_id, status[3], comment_to=reply)
        return await jarvis.client.delete_messages(message.chat_id, message.id)