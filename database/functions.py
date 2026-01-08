from database.database import Database
from config import jarvis_all, data_users
from json import dumps

async def save_settings(user_id):
    try:
        async with Database() as db:
            await db.execute("UPDATE profiles SET settings=$1 WHERE user_id=$2", (dumps(jarvis_all[data_users[user_id]].settings), user_id))
    except Exception as e:
        print("save_settings error: ",e)