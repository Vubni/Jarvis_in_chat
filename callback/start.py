from aiogram import Router, F

import keyboards.inline_kbs as kb

import functions.reg as func_reg
from database.database import Database
from aiogram.types import ReplyKeyboardRemove as KRemove
from aiogram.types import CallbackQuery
from FSM import fsm

from datetime import datetime
import pytz

from create_bot import moscow_tz
from core import time_passed_since

import config
from config import data_users, jarvis_all

from aiogram.types import FSInputFile, InputMediaPhoto

router_call = Router()

@router_call.callback_query(F.data.in_(['start', 'settings']))
async def menu(call: CallbackQuery):
    message = call.message
    await (await message.answer("Удаление кнопки...", reply_markup=KRemove())).delete()
    user_id = call.from_user.id
    if await func_reg.check_registration_user(user_id):
        return await message.edit_text("Привет👋\nНастройки и список команд бота:", reply_markup=kb.main())
    await message.edit_text(config.TEXT_MAIN, reply_markup=kb.new())
    

@router_call.callback_query(F.data == 'start_no_delete')
async def start_no_delete(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await call.answer("Переход в главное меню...")
    if await func_reg.check_registration_user(user_id):
        return await message.answer("Привет👋\nНастройки и список команд бота:", reply_markup=kb.main())
    await message.answer(config.TEXT_MAIN, reply_markup=kb.new())


@router_call.callback_query(F.data == 'page')
async def page(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    if await func_reg.check_registration_user(user_id):
        return await message.edit_text("Привет👋\nНастройки и список команд бота:", reply_markup=kb.main())
    await message.edit_text(config.TEXT_MAIN, reply_markup=kb.new())


@router_call.callback_query(F.data == 'commands')
async def modules(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    if await func_reg.check_registration_user(user_id):
        return await message.edit_text("Настройки команд:", reply_markup=kb.commands())

@router_call.callback_query(F.data == 'modules')
async def modules(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    if await func_reg.check_registration_user(user_id):
        return await message.edit_text("Настройки модулей:", reply_markup=kb.modules())
    

@router_call.callback_query(F.data == 'test')
async def test(call: CallbackQuery):
    await call.answer("В разработке 🛠️", True)

@router_call.callback_query(F.data == 'pro+')
async def pro(call: CallbackQuery):
    await call.answer("Доступно в подписках Pro и выше!", True)

@router_call.callback_query(F.data == 'only_business')
async def only_subscription(call: CallbackQuery):
    await call.answer("Доступно только в Джарвис Бизнес!", True)



@router_call.callback_query(F.data == 'reason_off')
async def reason_off(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await message.edit_text("Пожалуйста, напишите причину отключения бота")
    await fsm.register_next(fsm.Bot_off.reason, user_id)

@router_call.callback_query(F.data == 'use_promo_code')
async def use_promo_code(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await message.edit_text("Пожалуйста, <b>отправьте промокод</b>, который хотите применить или <b>отмените действие.</b>", reply_markup=kb.back("0_oplata"))
    await fsm.register_next(fsm.Oplata.promo, user_id)

@router_call.callback_query(F.data == '0_oplata')
async def use_promo_code(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await message.edit_text("<b>Хотите ли вы использовать промокод при оплате подписки?</b>", reply_markup=kb.promo())
    await fsm.register_next(fsm.Oplata.promo_0, user_id)



@router_call.callback_query(F.data == 'profile')
async def profile(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await fsm.delete_register(user_id)
    if not jarvis_all[data_users[user_id]].subscription:
        return await message.edit_text(f"""<b>🆔Ваш id telegram:</b> <code>{user_id}</code>
<b>📱Номер телефона:</b> <code>{jarvis_all[data_users[user_id]].phone_number}</code>

<b>⭐Информация о подписке:</b>
<b> ├ Тип:</b> Бесплатная
<b> ├ Подписка оформлена:</b> не указано
<b> ├ Действует до:</b> ∞
<b> ├ Куплена по цене:</b> Бесплатно
<b> └ Акция:</b> Не применялась""", reply_markup=await kb.profile(user_id))
        
    async with Database() as db:
        subscription = (await db.execute("SELECT subscription FROM profiles WHERE user_id=$1", (user_id,)))["subscription"]
    await message.edit_text(f"""<b>🆔Ваш id telegram:</b> <code>{user_id}</code>
<b>📱Номер телефона:</b> <code>{jarvis_all[data_users[user_id]].phone_number}</code>

<b>⭐Информация о подписке:</b>
<b> ├ Тип:</b> {subscription["type"]}
<b> ├ Подписка оформлена:</b> {subscription["date_subscription"] if subscription["date_subscription"] else "не указано"}
<b> ├ Действует до:</b> {subscription["paid_before"]}
<b> ├ Куплена по цене:</b> {subscription["by_price"]}⭐/месяц
<b> └ Акция:</b> {"Применялась" if subscription["is_stock"] else "Не применялась"}""", reply_markup=await kb.profile(user_id))

@router_call.callback_query(F.data == 'start_bot_need')
async def start_bot_need(call: CallbackQuery):
    await call.answer("Чтобы получить ссылку на чат с пользователями не имеющими юзернейм (пример: @username) требуется, чтобы они хоть раз запускали бота!", True)

@router_call.callback_query(F.data == 'imitation_1')
async def imitation_1(call: CallbackQuery):
    message = call.message
    await call.answer("Успешно!")
    await message.answer("""Было замечено <b><i>УДАЛЕНИЕ</i></b> сообщения❗
В личной переписке с '<a href='https://t.me/vubni_jarvis_bot'>Джарвис | Помощник в чатах!</a>' были удалены сообщения.
🗑️Было удалено 1 сообщение, оно содержало:
<blockquote>Привет! Я бот Джарвис!</blockquote>""", reply_markup=kb.del_msg("vubni_jarvis_bot"), disable_notification=True, disable_web_page_preview=True)
    
@router_call.callback_query(F.data == 'imitation_2')
async def imitation_2(call: CallbackQuery):
    message = call.message
    await call.answer("Успешно!")
    await message.answer("""Было замечено <b><i>РЕДАКТИРОВАНИЕ</i></b> сообщения❗
В личной переписке с '<a href='https://t.me/vubni_jarvis_bot'>Джарвис | Помощник в чатах!</a>' было отредактировано сообщение.

Исходное сообщение:
<blockquote>Привет! Я бот Джарвис!</blockquote>

🆕Новое сообщение:
<blockquote>Как тебе?</blockquote>""", reply_markup=kb.del_msg("vubni_jarvis_bot"), disable_notification=True, disable_web_page_preview=True)
    
@router_call.callback_query(F.data.startswith('sh|'))
async def smart_home(call: CallbackQuery):
    user_id = call.from_user.id
    if user_id not in data_users or data_users[user_id] not in jarvis_all:
        await call.answer("Умным домом может управлять только его владелец!", True)
        return
    await jarvis_all[data_users[user_id]].inline_call(call)

@router_call.callback_query(F.data == 'contacts')
async def contacts(call: CallbackQuery):
    message = call.message
    await message.edit_text("По вопросам функционала бота/сотрудничеству/ошибкам бота, писать -> @vubni.\n\nВремя ответа может варьироваться от 10 минут, до 2 часов в зависимости от занятости операторов и от типа обращения.",
                            reply_markup=kb.contacts())
    
@router_call.callback_query(F.data == 'connect_bot')
async def connect_bot(call: CallbackQuery):
    message = call.message
    await message.edit_text("""Для того, чтобы я начал работу - мне требуется подключиться к аккаунту телеграмм🤖

<b>В этом нет ничего страшного или опасного для тебя</b>, мы подключаемся строго по Telegram API и даже описали как и почему мы так подключаемся в <a href='https://vubni.gitbook.io/jarvis/osnovnaya-informaciya/quickstart'>статье</a>📃

Если у тебя остались сомнения, то ты можешь задать вопрос в комментарии <a href='https://t.me/jarvis_in_chat'>канала</a>, где <b>один из более 160 пользователей</b> обязательно ответит❤️‍🔥""",
                            reply_markup=kb.connect_bot())
    
@router_call.callback_query(F.data == 'referal')
async def referal(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await message.edit_text("Пригласи друга и тогда вы получите бонусы🎁\n<b>Другу</b> - <i>5 дней Pro</i>\n<b>Тебе</b> - <i>5 дней Pro или 1 день Бизнес</i>\n\n"
                            f"Твоя реферальная ссылка:\n<code>https://t.me/vubni_jarvis_bot?start=ref{user_id}</code>\n\n"
                            "<a href='https://vubni.gitbook.io/jarvis/menyu-bota-nastroiki/referalnaya-programma'>Подробнее про реферальную программу</a>",
                            reply_markup=kb.referal())
    
@router_call.callback_query(F.data == 'referal_del')
async def referal(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await message.delete()
    await message.answer("Пригласи друга и тогда вы получите бонусы🎁\n<b>Другу</b> - <i>5 дней Pro</i>\n<b>Тебе</b> - <i>5 дней Pro или 1 день Бизнес</i>\n\n"
                            f"Твоя реферальная ссылка:\n<code>https://t.me/vubni_jarvis_bot?start=ref{user_id}</code>\n\n"
                            "<a href='https://vubni.gitbook.io/jarvis/menyu-bota-nastroiki/referalnaya-programma'>Подробнее про реферальную программу</a>",
                            reply_markup=kb.referal())
    
@router_call.callback_query(F.data == 'referal_2')
async def referal(call: CallbackQuery):
    message = call.message
    await message.answer_photo(FSInputFile("images/logo.png"), caption="🚀 <b>Привет!</b>\n"
            "Я использую Джарвиса в чатах, и он становится незаменимым помощником <i>в каждом диалоге!</i>\n\n"
            "🌟 <b>Главные возможности:</b>\n"
            "<blockquote expandable>"
                "🔍 Просмотр удалённых сообщений и чатов\n"
                "📝 Просмотр изменённых сообщений\n"
                "🛡️ Антиспам система\n"
                "💬 Быстрые ответы\n"
                "🤖 Автоответчик\n"
                "💡 Управление умным домом\n"
                "☁️ Облако для сообщений\n"
                "📰 Ежедневные новости\n"
                "🎥 Создание кружков (видеосообщений)\n"
                "⌨️ Исправление раскладки\n"
                "🎧 Распознавание голосовых\n"
                "🧮 Встроенный калькулятор\n"
                "🔮 Синхронизация с Яндекс Алисой (скоро)"
            "</blockquote>\n\n"
            "🔥 <b>Хочешь такого же помощника?</b>\n"
            "👉 Подключай Джарвиса прямо сейчас: @vubni_jarvis_bot\n", reply_markup=kb.back("referal_del"))
    
@router_call.callback_query(F.data == 'stats')
async def statistics(call: CallbackQuery):
    message = call.message
    async with Database() as db:
        count = (await db.execute("SELECT COUNT(*) AS total_rows FROM profiles WHERE status=true"))["total_rows"]
        count_messages = (await db.execute("SELECT MAX(id) AS id FROM messages"))["id"]
    time_now = datetime.now(pytz.utc).astimezone(moscow_tz).strftime("%d.%m.%Y")
    await message.edit_text(f"""📊Актуальная статистика <a href='https://t.me/vubni_jarvis_bot'>Джарвиса</a> на <b>{time_now}</b>:

👥Текущее кол-во подключённых аккаунтов: <b>{count:,}</b>
💬<b>{count_messages:,}</b> сообщений я обработал за всё время!

🕒Бот работает уже <b>{time_passed_since(datetime(2024, 5, 25, 21, 26, 0))}</b>""".replace(",", " "), reply_markup=kb.back("page"), disable_web_page_preview=True)