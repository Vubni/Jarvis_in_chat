from telethon.tl import types
import asyncio



async def send_message_online(jarvis, func_send):
    user = await jarvis.client.get_me()
    while not isinstance(user.status, types.UserStatusOnline):
        await asyncio.sleep(5)
        user = await jarvis.client.get_me()
    await func_send