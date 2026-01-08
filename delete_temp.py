from database.database import Database
import config
import s3
from datetime import datetime, timedelta
import pytz

async def start():
    async with Database() as db:
        pro_days = int(config.LIMIT_DAY_TEMP['Pro'])
        free_days = int(config.LIMIT_DAY_TEMP[False])
        print(type(pro_days), pro_days, type(free_days), free_days)
        
        # Удаляем все записи и получаем все media_content (включая NULL)
        deleted_media = await db.execute(
            """
            DELETE FROM messages
            USING profiles
            WHERE messages.user_id = profiles.user_id
            AND messages.date < NOW() - INTERVAL '1 day' * 
                CASE 
                    WHEN profiles.subscription->>'type' = 'Pro' THEN $1
                    ELSE $2
                END
            RETURNING messages.media_content;
            """,
            (pro_days, free_days)
        )
        
        await db.execute("DELETE FROM open_web WHERE date < NOW() - INTERVAL '1 day'")
        
    media_contents = [row['media_content'] for row in deleted_media if row['media_content']]
    for media in media_contents:
        await s3.delete_object("files/" + media['media_content'])
    data = await s3.list_objects()
    for name, date in data.items():
        if date <= datetime.now(pytz.UTC) - timedelta(days=config.LIMIT_DAY_TEMP_S3):
            await s3.delete_object(name)