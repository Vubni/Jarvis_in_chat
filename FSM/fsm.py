from aiogram.fsm.context import FSMContext, StorageKey
from create_bot import memory_storage
from config import bot_id
from aiogram.fsm.state import State, StatesGroup
from core import cache_with_expiration

@cache_with_expiration(60*5)
def get_state(user_id, chat_id, thread_id):
    return FSMContext(memory_storage, StorageKey(bot_id, chat_id, user_id, thread_id))

async def register_next(object, user_id, chat_id=None, thread_id=None):
    if not chat_id:
        chat_id = user_id
    state = FSMContext(memory_storage, StorageKey(bot_id, chat_id, user_id, thread_id))
    data = await get_data(user_id, chat_id)
    await state.clear()
    await state.set_state(object)
    await set_data(data, user_id, chat_id)

async def delete_register(user_id, chat_id=None, thread_id=None):
    if not chat_id:
        chat_id = user_id
    state = FSMContext(memory_storage, StorageKey(bot_id, chat_id, user_id, thread_id))
    await state.clear()

async def set_data(kwargs, user_id, chat_id=None, thread_id=None):
    if not chat_id:
        chat_id = user_id
    state = FSMContext(memory_storage, StorageKey(bot_id, chat_id, user_id, thread_id))
    await state.update_data(kwargs)

async def get_data(user_id, chat_id=None, thread_id=None):
    if not chat_id:
        chat_id = user_id
    state = get_state(user_id, chat_id, thread_id)
    return await state.get_data()


class Prefix(StatesGroup):
    edit = State()

class Ping_check(StatesGroup):
    check = State()

class Oplata(StatesGroup):
    promo = State()
    promo_0 = State()
    version = State()

class Suggest_idea(StatesGroup):
    suggest = State()

class Attention_edit(StatesGroup):
    news = State()
    weat = State()
    utc = State()

class Quick_answer(StatesGroup):
    create = State()
    
class Bot_off(StatesGroup):
    reason = State()

class Answer_create(StatesGroup):
    text_from_set = State()
    answer_set = State()
    
class Antispam(StatesGroup):
    _except = State()

class Chats_settings(StatesGroup):
    chats_except = State()
    groups_except = State()
    
class Promo(StatesGroup):
    create = State()