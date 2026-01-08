from create_bot import bot
from functions.smart_home import Smart_home, Lamp_control
from telethon.tl import functions
from aiogram import Router, F
from aiogram.types import CallbackQuery
from config import jarvis_all, data_users

router_smart_home = Router()


@router_smart_home.callback_query(F.data.startswith("sh|"))
async def inline_call(call: CallbackQuery):
    user_id = call.from_user.id
    jarvis = jarvis_all[data_users[user_id]]
    if call.from_user.id != jarvis.user.id:
        bot.answer_callback_query(call.id, "Умным домом может управлять только его владелец!")
        return
    query = call.data.lower()
    home = Smart_home(jarvis.yandex_token)
    devices = home.get_devices()
    
    if "on" in query:
        bot.answer_callback_query(call.id, "Включено!")
    elif "off" in query:
        bot.answer_callback_query(call.id, "Выключено!")
    elif "color|0" in query:
        bot.answer_callback_query(call.id, "Выберите цвет ниже!")
        return
    elif "scene|0" in query:
        bot.answer_callback_query(call.id, "Установите сценарий для лампы!")
        return
    
    if "sh|" == query:
        inline_query = (await jarvis.client.inline_query("@vubni_jarvis_bot", query="smart_home", entity=call.message.chat.id)).result
        await jarvis.client(functions.messages.SendInlineBotResultRequest(
            peer=call.message.chat.id,
            query_id=inline_query.query_id,
            id=inline_query.results[0].id,
            hide_via=True
        ))
        return

    if "sh|" in query:
        id_device = int(query.split("|")[1])
        home = Smart_home(jarvis.yandex_token)
        devices = home.get_devices()
        if "devices.types.light" in devices[id_device]["type"]:
            lamp = Lamp_control(jarvis.yandex_token, devices[id_device]["id"])
            if lamp.state == "offline":
                bot.answer_callback_query(call.id, "Устройство не отвечает. Проверьте, что оно подключено к интернету!")
                return
            if "brig|0" in query:
                bot.answer_callback_query(call.id, f"Текущая яркость: {lamp.brightness}%")
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
        inline_query = (await jarvis.client.inline_query("@vubni_jarvis_bot", query=query, entity=call.message.chat.id)).result
        await jarvis.client(functions.messages.SendInlineBotResultRequest(
            peer=call.message.chat.id,
            query_id=inline_query.query_id,
            id=inline_query.results[0].id,
            hide_via=True
        ))
    bot.answer_callback_query(call.id, "Успешно")
    return