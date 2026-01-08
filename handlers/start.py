from json import load, dumps
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message

import keyboards.inline_kbs as kb

import functions.reg as func_reg
from database.database import Database
import config
from aiogram.types import ReplyKeyboardRemove as KRemove
from html import escape
from FSM import fsm

from create_bot import bot

router = Router()

@router.message(CommandStart())
async def start(message: Message, command: CommandObject):
    command_args: str = command.args
    await (await message.answer("Удаление кнопки...", reply_markup=KRemove())).delete()
    user_id = message.from_user.id
    if command_args:
        if "ref" in command_args:
            try:
                ref = int(command_args.split("ref")[1])
            except:
                return await message.answer("Некорректная ссылка!")
            if ref == user_id:
                return await message.answer("Ты не можешь использовать свою же реферальную ссылку!")
            async with Database() as db:
                result = await func_reg.check_registration_user(user_id)
                if result:
                    return await message.answer("Ты уже зарегистрирован в боте! Ты не можешь использовать чью-либо реферальную ссылку!")
                result = await func_reg.check_registration_user(ref)
                if not result:
                    return await message.answer("Реферальная ссылка недействительна!")
                settings = load(open('base_settings/base_settings.json', 'r', encoding='utf-8'))
                await db.execute("INSERT INTO profiles (user_id, settings, status, referal) VALUES ($1, $2, 0, $3)",
                                    (user_id, dumps(settings), ref))
                await message.answer("Успешно применена реферальная ссылка! После подключения бота, будет начислена Pro подписка!")
        elif "premium" in command_args and await func_reg.check_registration_user(user_id):
            await fsm.register_next(fsm.Oplata.promo_0, user_id)
            return await message.answer("*Хотите ли вы использовать промокод при оплате подписки?*",
                                        parse_mode="Markdown", reply_markup=kb.promo())
    if await func_reg.check_registration_user(user_id):
        return await message.answer("Привет👋\nНастройки и список команд бота:", reply_markup=kb.main())
    await message.answer(config.TEXT_MAIN, reply_markup=kb.new())
    

@router.message(Command("paysupport"))
async def paysupport(message: Message, command: CommandObject):
    await message.answer("""По поводу любого вопроса о транзакции или для обговорения условий возврата средств - обращайтесь к @Vubni.\n
For any question about the transaction or to discuss the terms of the refund, please contact @Vubni.""", reply_markup=kb.pay_support())

@router.channel_post(F.chat.id == -1002237639994)
async def handler_channel_post(message: Message):
    try:
        async with Database() as db:
            results = await db.execute_all("SELECT user_id FROM profiles WHERE settings @> $1", ('{"advertisement": true}',))
        for result in results:
            try:
                await bot.forward_message(result["user_id"], message.chat.id, message.message_id)
            except:
                pass
    except Exception as e:
        print(f"Error handler_channel_post: ", e)