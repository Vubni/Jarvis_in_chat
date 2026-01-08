from TelegramClient import Jarvis_client
from create_bot import bot
from FSM import fsm
from config import jarvis_all, data_users
from database.database import Database
from keyboards import inline_kbs as kb
import os, asyncio, config
from functions.functions import import_modules

async def create_client(phone):
    try:
        if phone in jarvis_all:
            if jarvis_all[phone].status:
                for phone_number, user_id in data_users.items():
                    if phone_number == phone:
                        await bot.send_message(user_id, "<b>Я успешно подключён!</b>🔥\n\n"
                               "Если тебя пугает, что Джарвис подключился к твоему аккаунту и отображается в устройствах, то можешь прочесть <a href='https://t.me/jarvis_in_chat/63'>пост</a> и убедиться, что подключён именно я!")
                        await bot.send_message(user_id, "Отправь 'пинг' для проверки соединения!")
                        await fsm.register_next(fsm.Ping_check.check, user_id)
                        return 1
                return 1
            else:
                return 0
        client = Jarvis_client(phone)
        await client.start()
        return 0
    except Exception as e:
        print("create_client error: ", e)
        return 2

async def start_client(phone):
    try:
        client = Jarvis_client(phone)
        await client.start()
    except Exception as e:
        print(e)

async def process_task(task):
    id_db, phone, user_id = task["id"], task["phone"], task["user_id"]
    print(f"Запуск id: {id_db} | phone: {phone} | user_id: {user_id}")
    try:
        client = Jarvis_client(phone)
        await client.start()
    except Exception as e:
        print(e)
        print("Ошибка при создании клиента!")
        if phone in jarvis_all:
            del jarvis_all[phone]
        if user_id in data_users:
            del data_users[user_id]
        try:
            client.scheduler.shutdown()
            del client
        except:
            pass
    
    if not client.status:
        await client.stop_func()
        if task["reason"] is None:
            try:
                try:
                    print("user_id: ", user_id, "  username: ", (await bot.get_chat(user_id)).user.username)
                except:
                    print("user_id: ", user_id)
                async with Database() as db:
                    await db.execute("UPDATE profiles SET status=false WHERE user_id=$1", (user_id,))
                
                try:
                    os.remove(f"./sessions/{phone}.session")
                except Exception as e:
                    print(e)

                await bot.send_message(user_id, 
                    "По какой-то причине <b>Джарвис не смог подключиться</b> к вашему аккаунту!\n<b>Требуется пройти подключение повторно!</b>\n\n"
                    "Если вы отключили Джарвис самостоятельно, то пожалуйста, напишите причину.", reply_markup=kb.connect_off())
            except Exception as e:
                print("Бот заблокирован.", e)

async def run_clients():
    try:
        async with Database() as db:
            secret = await db.execute_all("SELECT id, phone, user_id, reason FROM profiles WHERE status=true")
        tasks = [process_task(task) for task in secret]
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        print(f"Ошибка при работе с run_clients: ", e)



async def start():
    await run_clients()
    await asyncio.sleep(99999999900009)
    # status_start = True
    # for id_telegram in wait_to_start:
    #     start_bot_chat(id_telegram)
    # del wait_to_start
    #Надо ожидание чего-то
