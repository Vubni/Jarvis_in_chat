from json import load, dumps
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message

import keyboards.inline_kbs as kb

import functions.reg as func_reg
from database.database import Database
import config
from aiogram.types import ReplyKeyboardRemove as KRemove
from aiogram.types import CallbackQuery, LabeledPrice

from aiogram.types import InlineKeyboardMarkup as IMarkup
from aiogram.types import InlineKeyboardButton as IButton
from aiogram.filters import StateFilter

from FSM import fsm

from functions.payments import get_month_word
from create_bot import bot

router_call_fsm = Router()

@router_call_fsm.callback_query(F.data == 'use_promo_code', StateFilter(fsm.Oplata.promo_0, fsm.Oplata.version))
async def use_promo_code(call: CallbackQuery):
    message = call.message
    user_id = call.from_user.id
    await message.edit_text("<b>Пожалуйста, <b>отправьте промокод</b>, который хотите применить или <b>продолжайте без него.</b></b>", reply_markup=kb.back("0_oplata"))
    await fsm.register_next(fsm.Oplata.promo, user_id)


@router_call_fsm.callback_query(F.data == 'oplata', StateFilter(fsm.Oplata.promo_0, fsm.Oplata.version))
async def use_promo_code(call: CallbackQuery):
    user_id = call.from_user.id
    message = call.message
    async with Database() as db:
        prices = await db.execute_all("SELECT DISTINCT type FROM prices")
        bonus = 0
        inline_kb_list = []
        data = await fsm.get_data(user_id)
        if "promo_code" in data:
            bonus = (await db.execute("SELECT bonus FROM promo_codes WHERE code=$1", (data["promo_code"],)))["bonus"] / 100
        for row in prices:
            price_month = (await db.execute("SELECT price_month FROM prices WHERE price_month = (SELECT MIN(price_month) FROM prices WHERE type=$1) and type=$1", (row["type"],)))["price_month"]
            inline_kb_list.append([IButton(text=row["type"] + f" (От {int(price_month - (price_month * bonus))}⭐/месяц)", callback_data=f'oplata|{row["type"]}')])
    if not "promo_code" in data:
        inline_kb_list.append([IButton(text="Использовать промокод", callback_data="use_promo_code")])
    inline_kb = IMarkup(inline_keyboard=inline_kb_list)
    await message.edit_text("<b>Выбери интересующую вас подписку:</b>", reply_markup=inline_kb)
    await fsm.register_next(fsm.Oplata.version, user_id)

@router_call_fsm.callback_query(F.data.startswith('oplata|'), fsm.Oplata.version)
async def use_promo_code(call: CallbackQuery):
    user_id = call.from_user.id
    message = call.message
    version = call.data.split("|")[1]
    bonus = 0
    async with Database() as db:
        prices = await db.execute_all("SELECT * FROM prices WHERE type=$1 and NOT EXISTS (SELECT 1 FROM prices WHERE price_month = months)", (version,))
        data = await fsm.get_data(user_id)
        if "promo_code" in data:
            bonus = (await db.execute("SELECT bonus FROM promo_codes WHERE code=$1", (data["promo_code"],)))["bonus"]  / 100
    markup = []
    one_price = None
    for price in prices:
        if not one_price:
            one_price = price["price_month"]
        stock = price["is_stock"]
        price_all = price["price_month"] * price["months"]
        price_month = price["price_month"]
        months = price["months"]
        months_text = get_month_word(months)
        if months == 1 and stock is None:
            url = await bot.create_invoice_link(f"Джарвис {version} на {months_text}", 
                        f"Расширение функционала обычной версии с добавлением уникальных функций!    {months_text} подписки. {int(price_month - (price_month * bonus))}⭐/месяц",
                        f"{version}|{price_all}|{months}|{stock or bonus}|True", "XTR", 
                        [LabeledPrice(label=f"Джарвис {version} на {months_text}", amount=int(price_all - (price_all * bonus)))], subscription_period=2592000)
        else:
            url = await bot.create_invoice_link(f"Джарвис {version} на {months_text}", 
                    f"Расширение функционала обычной версии с добавлением уникальных функций!    {months_text} подписки. {int(price_month - (price_month * bonus))}⭐/месяц",
                    f"{version}|{price_all}|{months}|{stock or bonus}|False", "XTR", 
                    [LabeledPrice(label=f"Джарвис {version} на {months_text}", amount=int(price_all - (price_all * bonus)))])
        
        markup.append([IButton(text=f"{months_text} - {int(price_all - (price_all * bonus))} ⭐" + (" (Акция)" if stock else "") + \
                                        (f" (Скидка {int(100 - (price_month / one_price * 100))}%)" if months != 1 else ""), url=url, pay=True)])
    markup.append([IButton(text="Как выгодно купить ⭐?", url="https://vubni.gitbook.io/jarvis/osnovnaya-informaciya/oformlenie-podpiski")])
    markup.append([IButton(text="«", callback_data="oplata")])
    await message.edit_text("Выбери интересующую вас подписку:", reply_markup=IMarkup(inline_keyboard=markup))