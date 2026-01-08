
import delete_temp
import asyncio, requests
from create_bot import scheduler, bot
from apscheduler.triggers.interval import IntervalTrigger

def start():
    async def main():
        asyncio.create_task(delete_temp.start())
        scheduler.add_job(delete_temp.start, IntervalTrigger(hours=1), id='delete_temp')
        scheduler.start()
        print("Запуск систем. . .")
        result = requests.post("https://jarvis-chat.vubni.com/start_bot_jarvis")
        if result.status_code != 200:
            print(f"Ошибка запуска бота! Дополнительные сведенья:\n\nstatus_code: {result.status_code}, content: {result.content}")
            try:
                await bot.send_message(716452039, f"Ошибка запуска бота! Дополнительные сведенья:\n\nstatus_code: {result.status_code}, content: {result.content}", parse_mode=None)
            except:
                pass

    asyncio.run(main())