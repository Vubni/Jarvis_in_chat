from telethon import TelegramClient, events, errors
from telethon.tl import functions, types
import re
import os, time
import asyncio
from datetime import datetime, timedelta
import random, pytz
from collections import deque, defaultdict
from openai import OpenAI
from asyncio import create_task
from typing import Any, Union

from create_bot import bot, c_info
from FSM import fsm
from database.database import Database

from config import API_HASH, API_ID, data_users, jarvis_all, HEADERS, VERSION, logger
from functions.reg import register_func

from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from aiogram.types import CallbackQuery

from functions.smart_home import Smart_home, Lamp_control
from functions.antispam import is_spam
# from functions.anti_swear import is_swear
from functions.functions import clean_html, get_weather, get_crypto_price, LimitedSizeList, My_message, get_ad, create_promo
from functions import reg

from telethon.tl.patched import Message
from telethon.events.newmessage import NewMessage
from telethon.events.messageedited import MessageEdited
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telethon.events.messageedited import MessageEdited
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from keyboards import telegram_client as kb

from functions.check_commands_status import check_commands_status
from functions.messages import send_message_online
from sqlite3 import OperationalError
import uuid
from core import cache_with_expiration

import s3
import config
from functions import handler_deleted


class Jarvis_client:
    def __init__(self, phone_number):
        self.client = TelegramClient(os.path.join("./sessions/", f"{phone_number}.session"), API_ID, API_HASH, device_model='Jarvis in Chat', system_version='4.16.30-vxCUSTOM', app_version=VERSION, lang_code="ru", timeout=30)
        self.client.parse_mode = "html"
        
        self.phone_number = phone_number
        self.user = None
        self.status = False
        self.last_answer = time.time()
        
        self.password = False
        self.password_hint = None
        self.code = None
        self.code_attempt = 0
        self.phone_code_hash = None
        self.flood = False
        
        self.settings = None
        self.search_spammers = defaultdict(deque)
        self.old_message = {}
        self.spammer_list = {}
        self.jarvis_ai = []
        self.yandex_token = None
        self.last_inline = None
        self.modules_data = {}
        self.subscription = None

        self.ollama = OpenAI(
            base_url='http://localhost:11434/v1',
            api_key='ollama',
        )
        self.dialog = LimitedSizeList(6)

        self.edited_messages = {}

        self.scheduler = AsyncIOScheduler(timezone=pytz.utc)
        
    async def update_subscription(self):
        async with Database() as db:
            res = await db.execute("SELECT subscription FROM profiles WHERE user_id=$1", (self.user.id,))
        if not res["subscription"]:
            self.subscription = False
            return
        self.subscription = res["subscription"]["type"]
    
    async def auth(self, code=None, password=None):
        self.code_attempt += 1
        res = await self.auth_attemp(code, password)
        if code and not res and self.code_attempt == 5:
            self.code_attempt = 0
            await self.get_code_new()
        return res

    async def auth_attemp(self, code=None, password=None):
        if not self.phone_code_hash:
            return False
        try:
            if code and not self.password:
                await self.client.sign_in(self.phone_number, code, phone_code_hash=self.phone_code_hash)
            elif self.password and password:
                await self.client.sign_in(password=password)
        except errors.SessionPasswordNeededError:
            self.password = True
            self.password_hint = (await self.client(functions.account.GetPasswordRequest())).hint
            return True
        except errors.PhoneCodeInvalidError:
            return False
        except errors.FloodWaitError as e:
            self.flood = e.seconds
            return False
        except errors.PhoneCodeExpiredError:
            return False
        except errors.PasswordHashInvalidError:
            self.password = True
            return False
        
        
        if not (await self.client.is_user_authorized()):
            return False
        asyncio.create_task(self.uploading_messages())
        self.scheduler.remove_job("auto_delete")
        self.scheduler.shutdown()
        asyncio.create_task(self.wait_message())
        self.user = await self.client.get_me()
        await bot.send_message(self.user.id, "<b>Я успешно подключён!</b>🔥\n\n"
                               "Если тебя пугает, что Джарвис подключился к твоему аккаунту и отображается в устройствах, то можешь прочесть <a href='https://t.me/jarvis_in_chat/63'>пост</a> и убедиться, что подключён именно я!")
        await bot.send_message(self.user.id, "Отправь 'пинг' для проверки соединения!")
        await fsm.register_next(fsm.Ping_check.check, self.user.id)
        del self.code, self.code_attempt, self.password, self.password_hint, self.flood, self.phone_code_hash
        return True
    
    async def only_stop(self):
        try:
            await self.client.disconnect()
        except:
            pass

    async def stop_func(self):
        try:
            del data_users[self.user.id]
        except:
            pass
        try:
            await self.client.disconnect()
        except:
            pass
        try:
            del jarvis_all[self.phone_number]
        except:
            pass
        del self

    async def start(self):
        await self.client.connect()
        self.client.on(events.NewMessage)(self.new_message_handler)
        self.client.on(events.MessageDeleted)(self.deleted_message_handler)
        self.client.on(events.MessageEdited)(self.edited_message_handler)
        jarvis_all[self.phone_number] = self
        if not await self.client.is_user_authorized():
            print("Вызываю авторизацию: ", self.phone_number)
            try:
                self.phone_code_hash = (await self.client.send_code_request(self.phone_number, force_sms=False)).phone_code_hash
            except errors.FloodWaitError as e:
                self.flood = e.seconds
            except Exception as e:
                print("error send code: ", e)
            self.scheduler.add_job(self.auto_delete, IntervalTrigger(minutes=5), id='auto_delete')
            self.scheduler.start()
        else:
            self.status = True
            create_task(self.wait_message())
    
    async def get_code_new(self):
        try:
            self.phone_code_hash = (await self.client.send_code_request(self.phone_number, force_sms=False)).phone_code_hash
        except errors.FloodWaitError as e:
            self.flood = e.seconds
        except Exception as e:
            pass

    async def auto_delete(self):
        if await self.client.is_user_authorized():
            self.scheduler.remove_job("auto_delete")
            return
        self.scheduler.remove_job("auto_delete")
        try:
            del jarvis_all[self.phone_number]
        except:
            pass
        try:
            for key, value in data_users.items():
                if value == self.phone_number:
                    del data_users[key]
                    break
        except:
            pass
        try:
            await self.client.disconnect()
        except:
            pass
        del self
        return
         
    async def wait_message(self):
        self.user = await self.client.get_me()
        data_users[self.user.id] = self.phone_number
        await register_func(self.user.id, self.phone_number)
        await self.update_subscription()

        async with Database() as db:
            self.settings = (await db.execute("SELECT settings FROM profiles WHERE user_id=$1", (self.user.id,)))["settings"]

            result = await db.execute("SELECT yandex_token FROM smart_home WHERE user_id=$1", (self.user.id,))
            if result:
                self.yandex_token = result["yandex_token"]
        # asyncio.create_task(self.load_users_checker())
        asyncio.create_task(self.check_active())
        
        # Проверка, если вдруг бот заблокирован
        blocked = await self.client(functions.contacts.GetBlockedRequest(offset=0, limit=100))
        if any(user.id == config.bot_id for user in blocked.users):
            await self.client(functions.contacts.UnblockRequest(id=config.bot_id))
        
        
        # задачи в планировщик
        # self.scheduler.add_job(self.load_users_checker, IntervalTrigger(hours=6), id='load_users')
        self.scheduler.add_job(
            self.attention, 
            CronTrigger(hour=3, minute=0, timezone="UTC"), 
            id="attention"
        )
        self.scheduler.add_job(self.check_active, IntervalTrigger(hours=24), id='check_active')
        self.scheduler.add_job(check_commands_status, IntervalTrigger(days=1), (self,), id="check_commands_status")
        self.scheduler.start()
        
        try:
            async with self.client:
                await self.client.run_until_disconnected()
        except (errors.AuthKeyUnregisteredError, errors.AuthBytesInvalidError, FileNotFoundError, OperationalError) as e:
            print("client error: ", e)
            del jarvis_all[data_users[self.user.id]]
            del data_users[self.user.id]
            try:
                await self.client.disconnect()
            except:
                pass
            try:
                await bot.send_message(self.user.id, "<b>Джарвис успешно отключён от аккаунта</b>!\n<i>Если хотите подключить заново - пройдите подключение повторно!</i>\n\n"
                                       "Пожалуйста, укажите причину отключения Джарвис, чтобы мы смогли сделать его лучше!", reply_markup=kb.off_connect())
            except:
                pass
            async with Database() as db:
                await db.execute("UPDATE profiles SET status=false WHERE user_id=$1", (self.user.id,))

    async def load_users_checker(self):
        try:
            async with Database() as db:
                res = await db.execute("SELECT last_update FROM profiles WHERE user_id=$1", (self.user.id,))
                if res == datetime.now(pytz.UTC).date():
                    return
                await db.execute("UPDATE profiles SET last_update=CURRENT_DATE WHERE user_id=$1", (self.user.id,))
            await self.load_users()
        except Exception as e:
            print("load_users_checker: ", e)

    async def load_users(self):
        user_data = []
        async for dialog in self.client.iter_dialogs():
            if dialog.is_user:
                user = dialog.entity
                photo_exists = user.photo is not None
                dc_id = None
                if photo_exists:
                    dc_id = user.photo.dc_id
                status = datetime(1979, 1, 1)
                if not user.bot:
                    if isinstance(user.status, (types.UserStatusRecently, type(None))):
                        status = datetime(1999, 1, 1)
                    elif isinstance(user.status, types.UserStatusOffline):
                        status = user.status.was_online.date()  
                    elif isinstance(user.status, (types.UserStatusLastWeek, types.UserStatusOnline)):
                        status = datetime.now(pytz.UTC)
                    elif isinstance(user.status, types.UserStatusLastMonth):
                        status = datetime.now(pytz.UTC) - timedelta(days=7)
                user_data.append((user.id, user.phone,
                    user.bot, user.deleted,
                    user.verified, user.scam,
                    user.fake, user.premium,
                    photo_exists, status,
                    dc_id, user.lang_code))
                continue
            try:
                if isinstance(dialog.entity, types.ChatForbidden) or isinstance(dialog.entity, types.ChannelForbidden):
                    continue
                if dialog.entity.creator:
                    async for user in self.client.iter_participants(dialog):
                        photo_exists = user.photo is not None
                        dc_id = None
                        if photo_exists:
                            dc_id = user.photo.dc_id
                        status = datetime(1979, 1, 1)
                        if not user.bot:
                            if isinstance(user.status, (types.UserStatusRecently, type(None))):
                                status = datetime(1999, 1, 1)
                            elif isinstance(user.status, types.UserStatusOffline):
                                status = user.status.was_online.date()  
                            elif isinstance(user.status, (types.UserStatusLastWeek, types.UserStatusOnline)):
                                status = datetime.now(pytz.UTC)
                            elif isinstance(user.status, types.UserStatusLastMonth):
                                status = datetime.now(pytz.UTC) - timedelta(days=7)
                        user_data.append((user.id, user.phone,
                            user.bot, user.deleted,
                            user.verified, user.scam,
                            user.fake, user.premium,
                            photo_exists, status,
                            dc_id, user.lang_code))
            except Exception as e:
                print("load_users error: ", e)
        async with Database() as db:
            await db.executemany("""INSERT INTO users 
                (user_id, phone_number, is_bot, deleted, verified, scam, fake, premium, photo, status, dc_id, lang_code, last_updating) 
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, CURRENT_DATE)
                ON CONFLICT (user_id) DO UPDATE SET 
                phone_number = COALESCE(EXCLUDED.phone_number, users.phone_number), 
                is_bot = EXCLUDED.is_bot, 
                deleted = EXCLUDED.deleted, 
                verified = EXCLUDED.verified, 
                scam = EXCLUDED.scam, 
                fake = EXCLUDED.fake, 
                premium = EXCLUDED.premium, 
                photo = EXCLUDED.photo, 
                status = EXCLUDED.status, 
                lang_code = EXCLUDED.lang_code, 
                last_updating = CURRENT_DATE;""", user_data)
        
    async def edited_message_handler(self, event):
        if self.user is None:
            self.user = await self.client.get_me()
        if event.message.chat_id in self.spammer_list:
            return
        if isinstance(event.original_update, types.UpdateEditChannelMessage):
            return
        chat = await self.client.get_entity(event.message.chat_id)
        if isinstance(chat, types.Chat):
            return
        stats = True
        for item in self.settings["func_except"]:
            if item["id"] == event.message.chat_id:
                if not item["edit"]:
                    return
                stats = False
                break
        if stats and not self.settings["chats"]["edit"]:
            return
        create_task(self.edited_message(event))

    async def edited_message(self, event):
        start_time = time.time()
        self.edited_messages[event.message.id] = start_time
        await asyncio.sleep(1.1)
        if self.edited_messages[event.message.id] != start_time:
            return
        try:
            del self.edited_messages[event.message.id]
            if event.message.media:
                await self.edit_message_media(event)
            else:
                await self.edit_message(event)
        except Exception as e:
            print("Ошибка при фиксировании изменения сообщения: ", e)
        
    
    async def deleted_message_handler(self, event):
        if self.user is None:
            self.user = await self.client.get_me()
        if not self.subscription:
            create_task(handler_deleted.deleted_notification(self, event.deleted_ids[:config.LIMIT_DELETED], event))
        else:
            create_task(handler_deleted.deleted_notification(self, event.deleted_ids, event))
    
    async def is_spam(self, date: datetime, user_id):
        message_log = self.search_spammers[user_id]
        while message_log and message_log[0] < date - timedelta(seconds=3):
            message_log.popleft()
        message_log.append(date)
        temp = [8, 6, 4]
        if len(message_log) > temp[self.settings["antispam"]["sensitivity"] - 1]:
            self.search_spammers[user_id].clear()
            return True
        return False

    async def inline_call(self, call: CallbackQuery):
        if call.from_user.id != self.user.id:
            await call.answer("Умным домом может управлять только его владелец!", True)
            return
        query = call.data
        home = Smart_home(self.yandex_token)
        devices = home.get_devices()
        
        if "on" in query:
            await call.answer("Включено!")
        elif "off" in query:
            await call.answer("Выключено!")
        elif "color|0" in query:
            await call.answer("Выберите цвет ниже!")
            return
        elif "scene|0" in query:
            await call.answer("Установите сценарий для лампы!")
            return
        
        if "sh|" == query:
            if self.last_inline:
                await self.client.delete_messages(self.last_inline[0], self.last_inline[1])
            inline_query = (await self.client.inline_query("@vubni_jarvis_bot", query="smart_home", entity=self.last_inline[0])).result
            message_new = await self.client(functions.messages.SendInlineBotResultRequest(
                peer=self.last_inline[0],
                query_id=inline_query.query_id,
                id=inline_query.results[0].id,
                hide_via=True
            ))
            self.last_inline = [self.last_inline[0], message_new.updates[0].id]
            return

        if "sh|" in query:
            id_device = int(query.split("|")[1])
            home = Smart_home(self.yandex_token)
            devices = home.get_devices()
            if "devices.types.light" in devices[id_device]["type"]:
                lamp = Lamp_control(self.yandex_token, devices[id_device]["id"])
                if lamp.state == "offline":
                    await call.answer("Устройство не отвечает. Проверьте, что оно подключено к интернету!")
                    return
                if "brig|0" in query:
                    await call.answer(f"Текущая яркость: {lamp.brightness}%")
                    return

                if "|off" in query:
                    lamp.turn_off()
                elif "|on" in query:
                    lamp.turn_on()

                elif "|brig|" in query:
                    id_brig = int(query.split("|")[3])
                    if id_brig == 1:
                        lamp.set_brightness(1)
                    elif id_brig == 2:
                        lamp.set_brightness(50)
                    elif id_brig == 3:
                        lamp.set_brightness(100)
                    elif id_brig == 4:
                        lamp.edit_brightness(-25)
                    elif id_brig == 5:
                        lamp.edit_brightness(-10)
                    elif id_brig == 6:
                        lamp.edit_brightness(10)
                    elif id_brig == 7:
                        lamp.edit_brightness(25)

                if lamp.color:
                    if "|color|" in query:
                        id_color = int(query.split("|")[3])
                        if id_color == 1:
                            lamp.set_color(temperature_k=0)
                        elif id_color == 2:
                            lamp.set_color(temperature_k=9999)
                        elif id_color == 3:
                            lamp.set_color((255, 0, 0))
                        
                        if id_color == 4:
                            lamp.set_color((0, 0, 255))
                        elif id_color == 5:
                            lamp.set_color((139, 255, 0))
                        elif id_color == 6:
                            lamp.set_color((0, 255, 0))
                    
                        if id_color == 7:
                            lamp.set_color((150, 75, 0))
                        elif id_color == 8:
                            lamp.set_color((255, 165, 0))
                        elif id_color == 9:
                            lamp.set_color((255, 255, 0))

                if lamp.color_scene:
                    if "|scene|" in query:
                        id_scene = int(query.split("|")[3])
                        lamp.set_scene(lamp.color_scene[id_scene-1])
        if len(query.split("|")) < 3:
            inline_query = (await self.client.inline_query("@vubni_jarvis_bot", query=query, entity=self.last_inline[0])).result
            self.query_id = inline_query.query_id
            if self.last_inline:
                await self.client.delete_messages(self.last_inline[0], self.last_inline[1])
            message_new = await self.client(functions.messages.SendInlineBotResultRequest(
                peer=self.last_inline[0],
                query_id=inline_query.query_id,
                id=inline_query.results[0].id,
                hide_via=True
            ))
            self.last_inline[1] = message_new.updates[0].id
        await call.answer("Успешно!")
        return

    async def add_message(self, user_id, message, info):
        current_time = message.date.timestamp()  # Преобразуем datetime в timestamp
        # Если у пользователя нет сообщений, создаем новый список
        if user_id not in self.old_message:
            self.old_message[user_id] = []
        message_list = self.old_message[user_id]
        message_list = [msg for msg in message_list if current_time - msg["time"] <= 20]
        self.old_message[user_id] = message_list
        matching_count = sum(1 for msg in message_list if msg["info"] == info)
        if matching_count >= 2:
            return False  # Возвращаем False, если совпадает два сообщения
        message_list.append({"time": current_time, "info": info})
        self.old_message[user_id] = message_list
        if len(message_list) > 2:
            message_list.sort(key=lambda x: x["time"])  # Сортируем по времени
            message_list.pop(0)  # Удаляем самое старое сообщение
        return True  # Возвращаем True, если сообщение добавлено
    
    @cache_with_expiration(60)
    async def check_count_participants(self, chat_id):
        return (await self.client.get_participants(chat_id, limit=0)).total < self.settings["users_work_handler"]
    
    async def new_message_handler(self, event : NewMessage.Event, new_text=None):
        if self.user is None:
            self.user = await self.client.get_me()
        if not self.settings:
            try:
                async with Database() as db:
                    self.settings = (await db.execute("SELECT settings FROM profiles WHERE user_id=$1", (self.user.id,)))["settings"]

                    result = await db.execute("SELECT yandex_token FROM smart_home WHERE user_id=$1", (self.user.id,))
                    if result:
                        self.yandex_token = result["yandex_token"]
            except:
                print("Ошибка при получении настроек: ", self.user.id, self.phone_number)
                return
            
            
        message = event.message
        if new_text:
            event.message.text = new_text
        text = message.text.lower()
        chat = await event.get_chat()
        reply_message = None
        if message.reply_to:
            if not isinstance(message.reply_to, types.MessageReplyStoryHeader):
                reply_message = await message.get_reply_message()
        if '<a href="tg://user?id=6868690302">⁬</a>' in text or self.user.id == chat.id or chat.id == 777000 or (message.post and not message.forward):
            return
            
        # Если анонимное сообщение от нас - пишем что от нас
        try:
            from_user = await event.get_sender()
            if from_user is None or isinstance(from_user, types.Channel):
                if message.post or not message.out:
                    return
                from_user = self.user
            if from_user.bot:
                return
        except Exception as e:
            logger.warning("check anonymous message. ", e)
            return
        
        check_participant = True
        if not isinstance(chat, types.User):
            # Проверка на наличие нас в чате или ответ на наше сообщение
            if chat.left and (not reply_message or not reply_message.out):
                return
            # Проверка на кол-во участников
            check_participant = await self.check_count_participants(event.chat_id)
        
        #Если стикер = не спамим
        if from_user.id != self.user.id and chat.id != self.user.id and \
                            chat.id not in self.settings["antispam"]["except"] and \
                                (chat.__class__.__name__ in ['User'] and self.settings["antispam"]["status_chats"]) or \
                                    (chat.__class__.__name__ not in ['User'] and self.settings["antispam"]["status_groups"]):
            if event.message.sticker:
                if not await self.add_message(from_user.id, event.message, event.message.sticker.id):
                    await self.client.delete_messages(chat.id, event.message.id)
        


        if check_participant:
            if message.photo:
                create_task(self.save_media(message, from_user, "photo"))
            elif message.video_note:
                create_task(self.save_media(message, from_user, "video_note"))
            elif message.video:
                create_task(self.save_media(message, from_user, "video"))
            elif message.voice:
                create_task(self.save_media(message, from_user, "voice"))
            elif message.document:
                create_task(self.save_media(message, from_user, "document"))
            else:
                create_task(self.save_message(message, from_user, chat))

        #проверка на пересылаемое сообщение/сообщение от бота
        if message.forward or message.message == "" or not message.message or message.via_bot_id:
            return
        if message.reply_to:
            if isinstance(message.reply_to, types.MessageReplyStoryHeader):
                return
        

        if from_user.id != self.user.id and chat.id != self.user.id and \
                            chat.id not in self.settings["antispam"]["except"] and \
                                (chat.__class__.__name__ in ['User'] and self.settings["antispam"]["status_chats"]) or \
                                    (chat.__class__.__name__ not in ['User'] and self.settings["antispam"]["status_groups"]):
            if not (message.photo or message.video or message.document):
                if not await self.add_message(from_user.id, message, text):
                    await self.client.delete_messages(message.chat_id, message.id)

                if from_user.id in self.spammer_list:
                    temp = list(self.spammer_list.keys())
                    for keys in temp:
                        if from_user.id == keys:
                            if datetime.now(pytz.timezone('UTC')) >= self.spammer_list[keys]:
                                del self.spammer_list[keys]
                            else:
                                return
                if await self.is_spam(message.date, from_user.id):
                    if chat.__class__.__name__ in ['User'] and self.settings["antispam"]["status_chats"]:
                        time_new = timedelta(hours=1)
                        self.spammer_list[from_user.id] = datetime.now(pytz.timezone('UTC')) + time_new
                        result = await self.client(functions.account.GetNotifySettingsRequest(peer=chat))
                        if not result.mute_until or result.mute_until < datetime.now(pytz.timezone('UTC')):
                            await self.client(functions.account.UpdateNotifySettingsRequest(from_user,types.InputPeerNotifySettings(mute_until=time_new)))
                            await self.send_message(message, f"Я заметил спам в этом чате. Я <b>выключу уведомления</b> от этого чата и свой функционал для <b>{from_user.first_name} на 1 час.</b>")
                    elif self.settings["antispam"]["status_groups"] and self.subscription:
                        time_new = timedelta(hours=1)
                        self.spammer_list[from_user.id] = datetime.now(pytz.timezone('UTC')) + time_new
                        if chat.admin_rights:
                            if chat.admin_rights.ban_users:
                                try:
                                    await self.client.edit_permissions(message.chat_id, from_user.id, time_new, send_messages = False, send_media=False, send_gifs=False, send_stickers=False)
                                    await self.send_message(message, f"Я заметил спам в этом чате от <b>{from_user.first_name}</b>. Я замутил данного пользователя на 1 час.")
                                    return
                                except:
                                    pass
                        result = await self.client(functions.account.GetNotifySettingsRequest(peer=chat))
                        if not result.mute_until or result.mute_until < datetime.now(pytz.timezone('UTC')):
                            await self.client(functions.account.UpdateNotifySettingsRequest(chat, types.InputPeerNotifySettings(mute_until=time_new)))
                            bot.send_message(self.user.id, f"Я выключил уведомления в группе <b>{chat.title}</b> на 1 час, так как я заметил в ней спам.")

        stats = True
        for item in self.settings["func_except"]:
            if item["id"] == message.chat_id:
                if not item["command"]:
                    return
                stats = False
                break
        if not isinstance(chat, types.User):
            if not message.out or not self.subscription:
                return
            if stats and not self.settings["groups"]["command"]:
                return
        else:
            if stats and not self.settings["chats"]["command"]:
                return
            
        if time.time() - self.last_answer < 0.5:
            return
        
        if text == "!пинг":
            if from_user.id == self.user.id:
                return
            message.text = message.text[1:]
        elif from_user.id != self.user.id and await reg.check_registration_user(from_user.id):
            return

        event_message = My_message(event, message, from_user)
        await event_message.reply_message_init()
        for module in config.modules.values():
            try:
                if await module["main"].start(self, event_message):
                    break
            except Exception as e:
                print(f"error module new_message_handler for ", module["settings"].NAME, " : ", e)
    
    async def send_message(self, message : Message, text):
        try:
            reply = None
            if isinstance(message.reply_to, types.MessageReplyStoryHeader):
                return
            if message.reply_to and message.reply_to.forum_topic:
                if message.reply_to.reply_to_top_id:
                    reply = message.reply_to.reply_to_top_id
                elif message.reply_to.reply_to_msg_id and not message.reply_to.reply_to_top_id:
                    reply = message.reply_to.reply_to_msg_id
        except Exception as e:
            print("Ошибка при проверке не отвеченное ли сообщение: ", e)
            return
        if isinstance(message.peer_id, types.PeerUser):
            count = 2
        else:
            count = 1
        from_user = await self.client.get_entity(message.from_id)
        if not self.subscription:
            ad = await get_ad(from_user.id, count)
        else:
            ad = ""
        prefix = "<a href='https://t.me/vubni_jarvis_bot'>Джарвис: ⁬</a>"
        if self.subscription:
            prefix = self.settings["prefix"]["text"] + ": " if self.settings["prefix"]["status"] else ""
        return await self.client.send_message(message.chat_id, f"<a href='tg://user?id=6868690302'>⁬</a><b>{prefix}</b>" + text + "\n\n" + ad, comment_to=reply, silent=message.silent, link_preview=False)

    async def save_message(self, message, from_user, chat : Union[types.Channel, types.Chat]=False):
        if from_user.id == self.user.id:
            return
        async with Database() as db:
            if isinstance(chat, types.User) or not chat:
                user_check_sql = "INSERT INTO messages (user_firstname, user_id, message_id, text, username, from_user_id) VALUES($1, $2, $3, pgp_sym_encrypt($4, $5), $6, $7)"
                await db.execute(user_check_sql, (clean_html(from_user.first_name), self.user.id, message.id, clean_html(message.text), config.KEY_ENCRYPTION, from_user.username, from_user.id))
            else:
                user_check_sql = "INSERT INTO messages (user_firstname, user_id, message_id, text, username, from_user_id, chat_id) VALUES($1, $2, $3, pgp_sym_encrypt($4, $5), $6, $7, $8)"
                await db.execute(user_check_sql, (clean_html(from_user.first_name), self.user.id, message.id, clean_html(message.text), config.KEY_ENCRYPTION, from_user.username, from_user.id, chat.id))

    async def save_media(self, message, from_user, media_type, chat=False):
        if from_user.id == self.user.id:
            return

        media_map = {
            'photo': message.photo,
            'video': message.media,
            'voice': message.media,
            'video_note': message.media,
            'document': message.media
        }

        media = media_map.get(media_type)
        if not media:
            print(f"Это не {media_type}.")
            return

        original_filename = None  # Добавляем переменную для хранения имени файла

        # Определение размера и расширения файла
        if media_type == 'document':
            document = message.media.document
            file_name = next(
                (attr.file_name for attr in document.attributes 
                if isinstance(attr, types.DocumentAttributeFilename)),
                None
            )
            if not file_name:
                print("Не удалось определить имя файла.")
                return
            original_filename = file_name  # Сохраняем оригинальное имя
            file_size = document.size
            extension = os.path.splitext(file_name)[1]
        elif media_type == 'photo':
            try:
                photo_size = message.photo.sizes[-1]
                if isinstance(photo_size, types.PhotoSizeProgressive):
                    file_size = photo_size.sizes[-1]
                else:
                    file_size = photo_size.size
            except Exception as e:
                logger.error(f"save_photo error: {e} | photo: {message.photo}")
                return
            extension = '.jpg'
        elif media_type in ('video', 'video_note'):
            file_size = message.video.size
            extension = '.mp4'
        elif media_type == 'voice':
            duration = message.voice.attributes[0].duration
            file_size = duration * 16000  # Приблизительный размер для OPUS
            extension = '.ogg'
        else:
            print("Не поддерживаемый тип медиа.")
            return

        # Проверка размера файла до загрузки
        if not self.subscription and file_size > 20 * 1024 * 1024:
            return

        s3_key = f"{uuid.uuid4().hex}{extension}"
        mime_type = self._get_mime_type(media_type, media)

        # Формируем media_content с оригинальным именем для документов
        media_content = f"{media_type}={s3_key}"
        if media_type == 'document' and original_filename:
            media_content += f"|{original_filename}"  # Добавляем имя через |

        # Скачивание и загрузка медиа
        data = await self.client.download_media(media, bytes)
        if not data:
            print("Не удалось скачать медиа")
            return

        if not await s3.upload_bytes(data, "files/"+s3_key, mime_type):
            print("Ошибка загрузки на S3")
            return

        # Проверка лимита и сохранение в БД
        async with Database() as db:
            # Проверяем текущий лимит перед сохранением
            total_size = (await db.execute("SELECT COALESCE(SUM(file_size), 0) FROM messages WHERE user_id = $1 AND media_content IS NOT NULL", 
                (self.user.id,)))["coalesce"] or 0

            # Сохраняем новую запись с размером файла
            if isinstance(chat, types.User) or not chat:
                await db.execute(
                    """
                    INSERT INTO messages 
                    (user_firstname, user_id, message_id, text, media_content,
                    username, from_user_id, file_size) 
                    VALUES ($1, $2, $3, pgp_sym_encrypt($4, $5), $6, $7, $8, $9)
                    """,
                    (
                        clean_html(from_user.first_name),
                        self.user.id,
                        message.id,
                        clean_html(message.text),
                        config.KEY_ENCRYPTION,
                        media_content,
                        from_user.username,
                        from_user.id,
                        file_size
                    )
                )
            else:
                await db.execute(
                    """
                    INSERT INTO messages 
                    (user_firstname, user_id, message_id, text, media_content,
                    username, from_user_id, file_size, chat_id) 
                    VALUES ($1, $2, $3, pgp_sym_encrypt($4, $5), $6, $7, $8, $9, $10)
                    """,
                    (
                        clean_html(from_user.first_name),
                        self.user.id,
                        message.id,
                        clean_html(message.text),
                        config.KEY_ENCRYPTION,
                        media_content,
                        from_user.username,
                        from_user.id,
                        file_size,
                        chat.id
                    )
                )

            # Удаляем старые файлы если всё ещё превышаем лимит
            await self._cleanup_storage(db, total_size + file_size)
            
    def _get_mime_type(self, media_type, media):
        if media_type == 'document':
            return media.document.mime_type
        elif media_type == 'photo':
            return 'image/jpeg'
        else:
            return getattr(media.document, 'mime_type', 'application/octet-stream')

    async def _cleanup_storage(self, db: Database, current_total):
        if current_total <= config.LIMIT_BYTES_SIZE[self.subscription]:
            return

        # Получаем все медиа-записи, отсортированные по дате
        media_entries = await db.execute_all(
            "SELECT id, media_content, file_size FROM messages "
            "WHERE user_id = $1 AND media_content IS NOT NULL "
            "ORDER BY id DESC",
            (self.user.id,)
        )

        total = current_total
        for entry in media_entries:  # Удаляем самые старые
            if total <= config.LIMIT_BYTES_SIZE[self.subscription]:
                break
            total -= entry['file_size']
            await db.execute("DELETE FROM messages WHERE id = $1", (entry['id'],))
            await s3.delete_object("files/" + entry['media_content'].split('=', 1)[-1])

    async def edit_message(self, event: MessageEdited.Event):
        message = event.message
        async with Database() as db:
            result = await db.execute("SELECT * FROM messages WHERE message_id=$1 AND user_id=$2 AND chat_id is NULL", (message.id, self.user.id))
            if not result:
                return
            old_message = (await db.execute("SELECT pgp_sym_decrypt(text::bytea, $1) AS text FROM messages WHERE id=$2", (config.KEY_ENCRYPTION, result["id"])))["text"]
            await db.execute("UPDATE messages SET text=pgp_sym_encrypt($1, $2) WHERE id=$3", (clean_html(message.text), config.KEY_ENCRYPTION, result["id"]))
        if (old_message == clean_html(message.text) or not message.message or message.message == ""):
            return

        markup = []
        name = result["user_firstname"]
        text = "Было замечено <i><b>РЕДАКТИРОВАНИЕ</b></i> сообщения!\n"
        if result["username"]:
            url = f'https://t.me/{result["username"]}'
            text += f"В личной переписке с '<a href='{url}'>{name}</a>' было отредактировано сообщение.\n\n"
            markup.append([IButton(text='📬Перейти в личную переписку', url=url)])
        else:
            url = f'tg://user?id={message.peer_id.user_id}'
            try:
                await bot.get_chat(message.peer_id.user_id)
                markup.append([IButton(text='📬Перейти в личную переписку', url=url)])
            except:
                markup.append([IButton(text='Кнопка перехода не создана. Почему?', callback_data='start_bot_need')])
        markup.append([IButton(text='⚙️Настройки личных чатов', callback_data='monitored_chats')])
        new_message = clean_html(message.text)
        text = f"""В личной переписке с '<a href='{url}'>{name}</a>' было отредактировано сообщение.

<b>♻️Исходное сообщение:</b>
<blockquote expandable>{old_message}</blockquote>

<b>📨Новое сообщение:</b>
<blockquote expandable>{new_message}</blockquote>"""
        await bot.send_message(self.user.id, text, reply_markup=IMarkup(inline_keyboard=markup), disable_notification=True, disable_web_page_preview=True)
        
        
    async def edit_message_media(self, event):
        # Надо добавить чтобы отслеживало изменение изображений
        message = event.message
        async with Database() as db:
            result = await db.execute("SELECT * FROM messages WHERE message_id=$1 AND user_id=$2 AND chat_id is NULL", (message.id, self.user.id))
            if not result:
                return
            old_message = (await db.execute("SELECT pgp_sym_decrypt(text::bytea, $1) AS text FROM messages WHERE id=$2", (config.KEY_ENCRYPTION, result["id"])))["text"]
        if (old_message == clean_html(message.text) or not message.text or message.text == ""):
            return
            
        markup = []
        name = result["user_firstname"]
        text = "Было замечено <i><b>РЕДАКТИРОВАНИЕ</b></i> сообщения!\n"
        if result["username"]:
            url = f'https://t.me/{result["username"]}'
            text += f"В личной переписке с '<a href='{url}'>{name}</a>' было отредактировано сообщение.\n\n"
            markup.append([IButton(text='📬Перейти в личную переписку', url=url)])
        else:
            url = f'tg://user?id={message.peer_id.user_id}'
            try:
                await bot.get_chat(message.peer_id.user_id)
                markup.append([IButton(text='📬Перейти в личную переписку', url=url)])
            except:
                markup.append([IButton(text='Кнопка перехода не создана. Почему?', callback_data='start_bot_need')])
        markup.append([IButton(text='⚙️Настройки личных чатов', callback_data='monitored_chats')])
        new_message = clean_html(message.text)
        text = f"""В личной переписке с '<a href='{url}'>{name}</a>' было отредактировано сообщение.

<b>♻️Исходное сообщение:</b>
<blockquote expandable>{old_message}</blockquote>

<b>📨Новое сообщение:</b>
<blockquote expandable>{new_message}</blockquote>"""

        await bot.send_message(self.user.id, text, reply_markup=IMarkup(inline_keyboard=markup), disable_notification=True, disable_web_page_preview=True)
        async with Database() as db:
            await db.execute("UPDATE messages SET text=pgp_sym_encrypt($1, $2) WHERE id=$3", (new_message, config.KEY_ENCRYPTION, result["id"]))
        
    async def check_connect(self):
        try:
            self.user = await self.client.get_me()
            return True
        except:
            return False
    
    async def get_title_or_name(self, id):
        obj = await self.client.get_entity(id)
        if isinstance(obj, types.User):
            return obj.first_name
        return obj.title

    async def attention(self):
        if not self.settings["attention"]["status"]:
            return
        async with Database() as db:
            attention = await db.execute_all("SELECT * FROM attention WHERE (user_id=$1 OR user_id=0) AND (date=CURRENT_DATE OR date IS NULL)", (self.user.id,))
        if not attention:
            return
        user = await self.client.get_me()
        while not isinstance(user.status, types.UserStatusOnline):
            await asyncio.sleep(5)
            user = await self.client.get_me()
        
        full_user = await self.client(functions.users.GetFullUserRequest('me'))
        if full_user.full_user.birthday:
            birthday = datetime(datetime.now().year, full_user.full_user.birthday.month, full_user.full_user.birthday.day).date()
            promo = create_promo("СКИДКА", 25, 3)
            if datetime.now().date() == birthday:
                await bot.send_message(self.user.id, f"""🎉 С Днём Рождения! 🎂
Пусть этот день принесёт вам море улыбок, вдохновения и тепла близких людей! 🌟
Желаем, чтобы каждый момент года дарил радость, а мечты обретали крылья! ✨

🎁 Специальный подарок от нас:
Используйте промокод {promo} и получите скидку 25% на любую подписку в честь вашего праздника!
⏳ Акция действует 3 дня — не упустите возможность сделать этот день ещё ярче!

Спасибо, что вы с нами! 🥳
P.S. Не забудьте загадать желание — сегодня они точно сбываются! 💫""")
        
        for item in attention:
            text = item["text"]
            pattern = r'\[(.*?)\]'
            for match in re.findall(pattern, text):
                options = match.split(';')
                text = text.replace(f'[{match}]', random.choice(options).strip(), 1)
            
            if "%INFO%" in text:
                result_text = ""
                if self.settings["attention"]["news"]:
                    if not self.settings["attention"]["news_channel"]:
                        news_text = "<b>Новостной канал отсутствует</b>"
                    else:
                        try:
                            channel = await self.client.get_entity(self.settings["attention"]["news_channel"])
                            date = (datetime.now(pytz.UTC) - timedelta(days=1)).date()
                            all_messages = []
                            async for message in self.client.iter_messages(channel, limit=60, search=''):
                                if message.message == "":
                                    continue
                                if message.date.date() < date:
                                    break
                                if not is_spam(message.message):
                                    all_messages.append(message)
                            if len(all_messages) < 1:
                                text = text.replace("%NEWS%", "")
                            news = random.sample(all_messages, min(5, len(all_messages)))
                            if len(news) == 0:
                                news_text = "Не удалось получить новости, за последний день выбранный канал не публиковал постов."
                            else:
                                news_text = "<b>Рандомные новости:</b>"
                                for i in range(len(news)):
                                    if '@' not in str(self.settings["attention"]["news_channel"]):
                                        news_channel = str(self.settings["attention"]["news_channel"])[4:]
                                        news_text += "\n\n" + news[i].message.split("\n")[0] + f" <a href=https://t.me/c/{news_channel}/{news[i].id}>Пост</a>"
                                    else:
                                        news_channel = str(self.settings["attention"]["news_channel"])[1:]
                                        news_text += "\n\n" + news[i].message.split("\n")[0] + f" <a href=https://t.me/{news_channel}/{news[i].id}>Пост</a>"
                        except Exception as e:
                            print("attention, news: ", e)
                            news_text = "<b>Новостной канал отсутствует или не удалось получить новости!</b>"
                    result_text += news_text + "\n\n\n"

                if self.settings["attention"]["weather"]["status"]:
                    if not self.settings["attention"]["weather"]["city"]:
                        result_text += "Для погоды не выбран город!\n\n"
                    else:
                        # Замена % переменных
                        url = get_weather(self.settings["attention"]["weather"]["city"])
                        async with Database() as cursor:
                            id = db.fetchval("INSERT INTO open_web (url, date) VALUES ($1, $2)", (url, datetime.now(pytz.UTC).date()))
                        result_text += f"Погода доступна по <a href=https://t.me/vubni_jarvis_bot/url?startapp={id}>ссылке</a>\n\n"

                if self.settings["attention"]["currency"]:
                    usd = float(c_info.get_by_id("R01235").value)
                    euro = float(c_info.get_by_id("R01239").value)
                    btc, btc_percent = get_crypto_price("bitcoin")
                    eth, eth_percent = get_crypto_price("ethereum")
                    ton, ton_percent = get_crypto_price("the-open-network")
                    result_text += f"""<i>Курс валют и крипты:</i>
<b>• Доллар: {round(usd, 2):,}₽</b>
<b>• Евро: {round(euro, 2):,}₽</b>
<b>• Bitcoin: {round(btc * usd, 2):,}₽</b>
<b>• Etherium: {round(eth * usd, 2):,}₽</b>
<b>• Ton: {round(ton * usd, 2):,}₽</b>""".replace(",", " ")
                text = text.replace("%INFO%", result_text)
            
            try:
                await bot.send_message(self.user.id, clean_html(text), reply_markup=kb.attention(), disable_web_page_preview=True)
            except:
                try:
                    await self.client.send_message(config.bot_id, "/start")
                    await bot.send_message(self.user.id, clean_html(text), reply_markup=kb.attention(), disable_web_page_preview=True)
                except:
                    await self.stop_func()
            
        
    async def uploading_messages(self):
        now = datetime.now(pytz.UTC)
        three_days_ago = now - timedelta(days=3)

        # Получаем все диалоги
        async with Database() as db:
            async for dialog in self.client.iter_dialogs():
                if isinstance(dialog.entity, types.Channel) or isinstance(dialog.entity, types.Chat):
                    continue
                if dialog.entity.bot or dialog.entity.id == self.user.id:
                    continue
                async for message in self.client.iter_messages(dialog, reverse=True):
                    try:
                        if message.date >= three_days_ago:
                            from_user = await self.client.get_entity(message.from_id)
                            if from_user.id == self.user.id:
                                continue
                            await self.save_message(message, from_user)
                            res = await db.execute("SELECT * FROM messages WHERE user_id=$1, message_id=$2, from_user_id=$3", (self.user.id, message.id, from_user.id))
                            if res:
                                continue
                            user_check_sql = "INSERT INTO messages (user_firstname, user_id, message_id, text, username, date, from_user_id) VALUES($1, $2, $3, pgp_sym_encrypt($4, $5), $6, $7, $8)"
                            await db.execute(user_check_sql, (from_user.first_name, self.user.id, message.id, message.text, config.KEY_ENCRYPTION, from_user.username, message.date, from_user.id))
                        else:
                            break
                    except:
                        continue

    async def check_active(self):
        # Поиск последнего исходящего сообщения
        result = await self.client(functions.messages.SearchRequest(
            peer=types.InputPeerEmpty(),
            q='',
            from_id=self.user,
            filter=types.InputMessagesFilterEmpty(),
            min_date=None,
            max_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            hash=0,
            limit=1,
            add_offset=0
        ))
        
        messages = result.messages
        if messages:
            last_msg_date = messages[0].date
            delta = datetime.now(pytz.UTC) - last_msg_date
            days = delta.days
        else:
            days = 0 
        
        if days > 14:
            async with Database() as db:
                await db.execute("UPDATE profiles SET status=false WHERE user_id=$1", (self.user.id,))
            return await self.stop_func()
            
        if not self.subscription:
            return
        date_time = datetime.now(pytz.UTC)
        date_time = date_time.replace(hour=0, minute=0, second=0, microsecond=0)
        try:
            async with Database() as db:
                subscription = (await db.execute("SELECT subscription FROM profiles WHERE user_id=$1", (self.user.id,)))["subscription"]
                paid_before = datetime.strptime(subscription["paid_before"], '%Y-%m-%d').date()
                if paid_before < date_time.date():
                    await db.execute("UPDATE profiles SET subscription=NULL WHERE user_id=$1", (self.user.id,))
                    self.subscription = False
                    return await bot.send_message(self.user.id, "⏳ <b>Срок подписки истек!</b> \n💡 Теперь у тебя бесплатный доступ к Джарвису!\n🔄 Если хочешь продлить подписку - нажми кнопку ниже, чтобы обновить доступ", 
                                                reply_markup=kb.subscription())
                days = (paid_before - date_time.date()).days
                if days < 3:
                    if days == 0:
                        return bot.send_message(self.user.id, "<b>Внимание❗ Подписка закончится завтра.</b>\nДля продления нажмите кнопку ниже:", reply_markup=kb.subscription())
                    days += 1
                    await bot.send_message(self.user.id, "<b>Внимание❗ Подписка закончится через " + str(days) + " дня.</b>\nДля продления нажмите кнопку ниже:", reply_markup=kb.subscription())
        except Exception as e:
            logger.error("Ошибка check_active: ", e)