import os, asyncio
from aiohttp import web
from TelegramClient import jarvis_all, data_users
import clients_run as bot
import aiogram_run, run, clients_run
import threading, config, mimetypes
from functions.functions import import_modules, convert_seconds
from database.database import Database

status_bots = None

# Function to handle POST requests for new clients
async def handle_new_client(request):
    try:
        request_data = await request.json()
        phone = request_data.get('phone_number')

        # Run the coroutine to create a new client
        await bot.create_client(phone)

        if jarvis_all[phone].status:
            return web.Response(status=200)
        return web.Response(status=201)
    except Exception as e:
        print("handle_new_client error: ", e)
        return web.Response(status=520, text=str(e))

# Function to handle POST requests for creating connections
async def handle_create_connect(request):
    try:
        request_data = await request.json()
        phone = request_data.get('phone')

        if not phone:
            return web.Response(status=520)

        res = await bot.create_client(phone)
        
        if res == 1:
            return web.Response(status=400)
        elif res == 2:
            return web.Response(status=520)

        if jarvis_all[phone].status:
            return web.Response(status=200)

        return web.Response(status=201)
    except Exception as e:
        print("handle_create_connect error: ", e)
        return web.Response(status=500, text=str(e))

# Function to handle POST requests for getting password hint
async def handle_get_password_hint(request):
    try:
        request_data = await request.json()
        phone = request_data.get('phone')

        if jarvis_all[phone].password_hint:
            return web.json_response({
                "status": 200,
                "hint": jarvis_all[phone].password_hint
            }, status=200)

        return web.Response(status=404)
    except Exception as e:
        return web.Response(status=500, text=str(e))

# Function to handle POST requests for setting code
async def handle_set_code(request):
    try:
        request_data = await request.json()
        phone = request_data.get('phone')
        code = request_data.get('code')

        if not code or not phone:
            return web.Response(status=520)

        res = await jarvis_all[phone].auth(code=code)

        if not res:
            if jarvis_all[phone].flood:
                return web.Response(status=301, text=convert_seconds(jarvis_all[phone].flood))
            return web.Response(status=401)

        try:
            if jarvis_all[phone].password:
                return web.Response(status=201)
        except:
            pass
        
        return web.Response(status=200)
    except Exception as e:
        print("handle_set_code error: ", e)
        return web.Response(status=500, text=str(e))

# Function to handle POST requests for setting password
async def handle_set_password(request):
    try:
        request_data = await request.json()
        phone = request_data.get('phone')
        password = request_data.get('password')

        res = await jarvis_all[phone].auth(password=password)

        if res:
            return web.Response(status=200)
        return web.Response(status=401)
    except Exception as e:
        print("handle_set_password error: ", e)
        return web.Response(status=500, text=str(e))
    
async def handle_start_bot(request):
    global status_bots
    try:
        config.modules = import_modules()
        if status_bots:
            status_bots.cancel()
        else:
            asyncio.create_task(clients_run.start())
        status_bots = asyncio.create_task(aiogram_run.start())
        return web.Response(status=200)
    except Exception as e:
        print(e)
        return web.Response(status=500, text=str(e))


async def handle_open_web(request):
    param = request.query.get('tgWebAppStartParam', '')
    if param:
        async with Database() as db:
            res = await db.execute("SELECT url FROM open_web WHERE id=$1", (int(param),))
        if not res:
            return
        url = res["url"]
        raise web.HTTPFound(url)

# Function for serving static files
async def handle_get_file(request):
    path = request.match_info.get('path', '')
    
    # Остальная логика для других путей
    if path.endswith('.py'):
        return web.Response(status=404, text='404 Not Found: File not found')

    file_path = os.path.join(os.getcwd(), path.lstrip('/'))
    
    if os.path.isdir(file_path):
        index_path = os.path.join(file_path, 'index.html')
        if os.path.isfile(index_path):
            file_path = index_path
        else:
            return web.Response(status=404, text='404 Not Found: Directory index not found')

    if os.path.isfile(file_path):
        content_type, _ = mimetypes.guess_type(file_path)
        with open(file_path, 'rb') as f:
            return web.Response(body=f.read(), content_type=content_type or 'application/octet-stream')
    else:
        return web.Response(status=404, text='404 Not Found: File not found')

# Function to guess content type based on file extension
def guess_content_type(file_path):
    if file_path.endswith('.html'):
        return 'text/html'
    elif file_path.endswith('.css'):
        return 'text/css'
    elif file_path.endswith('.js'):
        return 'application/javascript'
    elif file_path.endswith('.png'):
        return 'image/png'
    elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
        return 'image/jpeg'
    elif file_path.endswith('.gif'):
        return 'image/gif'
    else:
        return 'application/octet-stream'


# def start():
#     app = web.Application()
#     app.router.add_post('/new_client', handle_new_client)
#     app.router.add_post('/create_connect', handle_create_connect)
#     app.router.add_post('/get_password_hint', handle_get_password_hint)
#     app.router.add_post('/set_code', handle_set_code)
#     app.router.add_post('/set_password', handle_set_password)
#     app.router.add_get('/{path:.*}', handle_get_file)

#     web.run_app(app, host=os.environ.get('INSTANCE_HOST'), port=int(os.environ.get('PORT')))
    # socket_path = os.environ.get('SOCKET')

    # if os.path.exists(socket_path):
    #     os.unlink(socket_path)

    # runner = web.AppRunner(app)
    # await runner.setup()
    # site = web.UnixSite(runner, socket_path)
    # await site.start()
    
    # print(f"Listening on {socket_path}")
    
    # try:
    #     while True:
    #         await asyncio.sleep(3600)  # Сохраняем выполнение сервера
    # except asyncio.CancelledError:
    #     pass
    # finally:
    #     await runner.cleanup()


# # Main entry point for running the server
if __name__ == "__main__":
    app = web.Application()
    app.router.add_post('/new_client', handle_new_client)
    app.router.add_post('/create_connect', handle_create_connect)
    app.router.add_post('/get_password_hint', handle_get_password_hint)
    app.router.add_post('/set_code', handle_set_code)
    app.router.add_post('/set_password', handle_set_password)
    app.router.add_post('/start_bot_jarvis', handle_start_bot)
    
    app.router.add_get('/open_web/', handle_open_web)
    app.router.add_get('/{path:.*}', handle_get_file)
    threading.Thread(None, run.start).start()
    print("Запуск сервера. . .")
    web.run_app(app, host=os.environ.get('INSTANCE_HOST'), port=int(os.environ.get('PORT')))