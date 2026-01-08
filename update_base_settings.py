from database.database import Database
import asyncio, time
from json import dumps


async def main():
    async with Database() as db:
        test = time.perf_counter()
        users = await db.execute_all("SELECT id, settings FROM profiles")
        indx = 0
        for user in users:
            indx += 1
            print(indx)
            settings = user["settings"]
            settings["modules"]["group_management"] = True
            await db.execute("UPDATE profiles SET settings=$1 WHERE id=$2", (dumps(settings), user["id"]))

if  __name__ == "__main__":
    asyncio.run(main())