from aiogram import Router, F

import keyboards.inline_kbs as kb

import functions.reg as func_reg
from database.database import Database

from aiogram.types import ReplyKeyboardRemove as KRemove
from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton

from aiogram.types import CallbackQuery
from FSM import fsm

from datetime import datetime
import pytz

from create_bot import moscow_tz
from core import time_passed_since

import config
from config import data_users, jarvis_all

from aiogram.types import FSInputFile, InputMediaPhoto

from datetime import datetime, timedelta
from functions.functions import generate_random_name

router_admins = Router()

@router_admins.callback_query(F.data.startswith('adm_cancel'))
async def adm_cancel(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await fsm.delete_register(user_id)
    await message.answer("🛡️Администратор. Действие отменено.")
    await admin_panel(call)


@router_admins.callback_query(F.data == 'admin_panel')
async def admin_panel(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    inline_kb = []
    level_admin = await func_reg.get_admin(user_id)
    if level_admin == 10:
        inline_kb.append([
            IButton(text="🔍 Поиск пользователя в системе", callback_data="adm_search_user"),
            IButton(text="🔄 Перезапуск бота", callback_data="adm_restart_bot")])
    if level_admin >= 5:
        inline_kb.append([
            IButton(text="📢 Оповещения для всех", callback_data="adm_send_alert"),
            IButton(text="📊 Настроить рекламу", callback_data="adm_setup_ads")])
    if level_admin >= 3:
        inline_kb.append([
            IButton(text="🛡️ Создать промокод", callback_data="adm_create_promo")])
    if level_admin >= 5:
        inline_kb.append([
            IButton(text="🛑 Экстренная остановка", callback_data="adm_emergency_stop")])
    inline_kb.append([
            IButton(text="«", callback_data="profile")])
    await message.edit_text("🛡️Администратор. Пожалуйста, выберите тип промокода:", reply_markup=IMarkup(inline_keyboard=inline_kb))


@router_admins.callback_query(F.data == 'adm_create_promo')
async def adm_create_promo(call: CallbackQuery):
    message = call.message
    inline_kb = [[IButton(text="Выдать Pro", callback_data="admin|prom|pro"), IButton(text="Выдать скидку", callback_data="admin|prom|disc")],
        [IButton(text="«", callback_data="admin_panel")]]
    await message.edit_text("🛡️Администратор. Пожалуйста, выберите тип промокода:", reply_markup=IMarkup(inline_keyboard=inline_kb))

    
@router_admins.callback_query(F.data.startswith('admin|prom|'))
async def admin_prom(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    data = call.data.replace("admin|prom|", "")
    await fsm.register_next(fsm.Promo.create, user_id)
    await fsm.set_data({"type": data}, user_id)
    inline_kb = [[IButton(text="5", callback_data="admin|prom_set|5"), IButton(text="10", callback_data="admin|prom_set|10"), IButton(text="15", callback_data="admin|prom_set|15")],
            [IButton(text="20", callback_data="admin|prom_set|20"), IButton(text="25", callback_data="admin|prom_set|25"), IButton(text="30", callback_data="admin|prom_set|30")],
            [IButton(text="40", callback_data="admin|prom_set|40"), IButton(text="50", callback_data="admin|prom_set|50"), IButton(text="60", callback_data="admin|prom_set|60")],
            [IButton(text="70", callback_data="admin|prom_set|70"), IButton(text="75", callback_data="admin|prom_set|75"), IButton(text="80", callback_data="admin|prom_set|80")],
            [IButton(text="90", callback_data="admin|prom_set|90"), IButton(text="99", callback_data="admin|prom_set|99")],
            [IButton(text="«", callback_data="adm_cancel")]]
    if data == "pro":
        inline_kb = [[IButton(text="3", callback_data="admin|prom_set|3"), IButton(text="5", callback_data="admin|prom_set|5"), IButton(text="7", callback_data="admin|prom_set|7")],
            [IButton(text="10", callback_data="admin|prom_set|10"), IButton(text="14", callback_data="admin|prom_set|14"), IButton(text="15", callback_data="admin|prom_set|15")],
            [IButton(text="30", callback_data="admin|prom_set|30"), IButton(text="60", callback_data="admin|prom_set|60"), IButton(text="90", callback_data="admin|prom_set|90")],
            [IButton(text="180", callback_data="admin|prom_set|180"), IButton(text="360", callback_data="admin|prom_set|360"), IButton(text="99999999", callback_data="admin|prom_set|99999999")],
            [IButton(text="«", callback_data="adm_cancel")]]
        return await message.edit_text("🛡️Администратор. Выберите количество дней, которое будет действовать <b>подписка</b>!", reply_markup=IMarkup(inline_keyboard=inline_kb))
    await message.edit_text("🛡️Администратор. Выберите процент скидки, который будет давать промокод!", reply_markup=IMarkup(inline_keyboard=inline_kb))

@router_admins.callback_query(F.data.startswith('admin|prom_set|'))
async def admin_prom_set(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    data = int(call.data.replace("admin|prom_set|", ""))
    await fsm.set_data({"bonus": data}, user_id)
    inline_kb = [[IButton(text="1", callback_data="admin|prom_day|1"), IButton(text="2", callback_data="admin|prom_day|2"), IButton(text="3", callback_data="admin|prom_day|3")],
            [IButton(text="5", callback_data="admin|prom_day|5"), IButton(text="7", callback_data="admin|prom_day|7"), IButton(text="10", callback_data="admin|prom_day|10")],
            [IButton(text="15", callback_data="admin|prom_day|15"), IButton(text="30", callback_data="admin|prom_day|30"), IButton(text="60", callback_data="admin|prom_day|60")],
            [IButton(text="90", callback_data="admin|prom_day|90"), IButton(text="180", callback_data="admin|prom_day|180"), IButton(text="360", callback_data="admin|prom_day|360")],
            [IButton(text="99999999", callback_data="admin|prom_day|99999999")],
            [IButton(text="«", callback_data="adm_cancel")]]
    await message.edit_text("🛡️Администратор. Выберите количество дней, сколько будет действовать <b>промокод</b>!", reply_markup=IMarkup(inline_keyboard=inline_kb))
    
@router_admins.callback_query(F.data.startswith('admin|prom_day|'))
async def admin_prom_set(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    data = datetime.now() + timedelta(days=int(call.data.replace("admin|prom_day|", "")))
    await fsm.set_data({"limit_day": data}, user_id)
    inline_kb = [[IButton(text="1", callback_data="admin|res|1"), IButton(text="2", callback_data="admin|res|2"), IButton(text="3", callback_data="admin|res|3")],
            [IButton(text="5", callback_data="admin|res|5"), IButton(text="7", callback_data="admin|res|7"), IButton(text="10", callback_data="admin|res|10")],
            [IButton(text="15", callback_data="admin|res|15"), IButton(text="30", callback_data="admin|res|30"), IButton(text="50", callback_data="admin|res|50")],
            [IButton(text="100", callback_data="admin|res|100"), IButton(text="1000", callback_data="admin|res|1000"), IButton(text="99999999", callback_data="admin|res|99999999")],
            [IButton(text="«", callback_data="adm_cancel")]]
    await message.edit_text("🛡️Администратор. Выберите, сколько создать промокодов!", reply_markup=IMarkup(inline_keyboard=inline_kb))
    
    
@router_admins.callback_query(F.data.startswith('admin|res|'))
async def admin_prom_set(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    count = int(call.data.replace("admin|res|", ""))
    data = await fsm.get_data(user_id)
    await fsm.delete_register(user_id)
    if data["type"] == "disc":
        data["type"] = "СКИДКА"
    else:
        data["type"] = "Pro"
        
    async with Database() as db:
        promo = generate_random_name(7)
        await db.execute("INSERT INTO promo_codes (code, type, bonus, count, limit_day) VALUES ($1, $2, $3, $4, $5)", (promo, data["type"], data["bonus"], count, data["limit_day"]))
    await message.answer(f"🛡️Администратор. <b>Промокод успешно создан!</b>\n<code>{promo}</code>")
    await admin_panel(call)
    