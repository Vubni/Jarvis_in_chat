from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import config
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import os, asyncio, pytz
from cbrf.models import DailyCurrenciesRates

c_info = DailyCurrenciesRates()

temp_jarvis = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_jarvis')
cloud = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cloud')

moscow_tz = pytz.timezone('Europe/Moscow')

scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
config.bot_id = bot.id

memory_storage = MemoryStorage()
dp = Dispatcher(storage=memory_storage)

# print("Импорт глобальных модулей. . .")
# directory_path = './modules'  # Укажите путь к вашей папке
# loaded_classes = load_classes_from_directory(directory_path)

# for class_name, class_ in loaded_classes.items():
#     print("Импортирован: ", class_name)