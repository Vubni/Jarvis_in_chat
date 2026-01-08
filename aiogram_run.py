import asyncio
import os
import config
from create_bot import bot, dp
from handlers.start import router
from handlers.handlers_fsm import router_fsm
from callback.start import router_call
from callback.call_fsm import router_call_fsm
from callback.settings_chats import router_call_settings_chats
from callback.settings import router_call_settings
from callback.offers import router_call_offers
from callback.other import router_call_other
from inline.inline_query import router_inline
from payment.payment import router_payment
# from work_time.time_func import send_time_msg
from database.database import Database
from web_app.main import router_web_app
from callback.smart_home import router_smart_home

from callback.admins import router_admins
from handlers.admin import router as router_admins_h

async def start():
    # Регистрация статических роутеров
    dp.include_router(router_fsm)
    dp.include_router(router)

    dp.include_router(router_admins)
    dp.include_router(router_admins_h)
    
    dp.include_router(router_call_fsm)
    dp.include_router(router_call_settings_chats)
    dp.include_router(router_call)
    dp.include_router(router_call_settings)
    dp.include_router(router_call_offers)
    dp.include_router(router_smart_home)
    
    dp.include_router(router_inline)
    dp.include_router(router_payment)
    
    dp.include_router(router_web_app)

    for item in config.modules:
        try:
            dp.include_router(config.modules[item]["settings"].router)
        except Exception as e:
            print(f"Error loading module {item}: {str(e)}")

    dp.include_router(router_call_other)
    # Запуск бота
    # await bot.delete_webhook(drop_pending_updates=False)
    while True:
        try:
            await dp.start_polling(bot)
        except Exception as e:
            print(f"Bot crashed: {e}. Restarting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(start())