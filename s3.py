# s3.py
import aioboto3
from botocore.exceptions import ClientError, NoCredentialsError
from config import BUCKET, s3_config
import hashlib
import asyncio
from aiobotocore.config import AioConfig

async def get_s3_client():
    """Возвращает новый S3 клиент для каждого вызова"""
    return aioboto3.Session().client('s3', 
        **s3_config, 
        config=AioConfig(
                signature_version='s3v4',
                connect_timeout=5,
                read_timeout=10,
                retries={'max_attempts': 3}
            )
    )

async def upload_bytes(
    bytes_data: bytes,
    file_name: str,
    mime_type: str = None
) -> bool:
    sha256_hash = hashlib.sha256(bytes_data).hexdigest()
    params = {
        'Bucket': BUCKET,
        'Key': file_name,
        'Body': bytes_data,
        'ChecksumSHA256': sha256_hash
    }
    
    if mime_type:
        params['ContentType'] = mime_type
    
    async with await get_s3_client() as s3:
        await s3.put_object(**params)
    return True

async def download_file(s3_key: str, local_path: str) -> bool:
    try:
        async with await get_s3_client() as s3:
            await s3.download_file(BUCKET, s3_key, local_path)
        return True
    except ClientError as e:
        print(f"Ошибка скачивания: {e}")
        return False

async def delete_object(s3_key: str) -> bool:
    try:
        async with await get_s3_client() as s3:
            await s3.delete_object(Bucket=BUCKET, Key=s3_key)
        return True
    except ClientError as e:
        print(f"Ошибка удаления: {e}")
        return False

async def get_metadata(s3_key: str) -> dict:
    try:
        async with await get_s3_client() as s3:
            response = await s3.head_object(Bucket=BUCKET, Key=s3_key)
        return {
            'Content-Type': response['ContentType'],
            'Content-Length': response['ContentLength'],
            'LastModified': response['LastModified']
        }
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return None
        print(f"Ошибка метаданных: {e}")
        return None

async def list_objects(prefix: str = '') -> dict:
    async with await get_s3_client() as s3:
        paginator = s3.get_paginator('list_objects_v2')
        all_objects = {}
        async for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
            for obj in page.get('Contents', []):
                all_objects[obj['Key']] = obj["LastModified"]
        return all_objects

async def copy_object(src_key: str, dest_key: str) -> bool:
    try:
        async with await get_s3_client() as s3:
            await s3.copy_object(
                CopySource={'Bucket': BUCKET, 'Key': src_key},
                Bucket=BUCKET,
                Key=dest_key
            )
        return True
    except ClientError as e:
        print(f"Ошибка копирования: {e}")
        return False

async def object_exists(s3_key: str) -> bool:
    try:
        async with await get_s3_client() as s3:
            await s3.head_object(Bucket=BUCKET, Key=s3_key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        raise

async def generate_presigned_url(object_name: str, expiration: int = 180) -> str:
    try:
        async with await get_s3_client() as s3:
            url = await s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET, 'Key': object_name},
                ExpiresIn=expiration
            )
        return url
    except NoCredentialsError:
        return None

async def test():
    test_key = "async_test.txt"
    copy_key = "async_test_copy.txt"
    
    # Тест загрузки
    print("Тест загрузки:", await upload_bytes(b"test data", test_key, "text/plain"))
    
    # Проверка существования
    print("Существует объект:", await object_exists(test_key))
    
    # Тест метаданных
    metadata = await get_metadata(test_key)
    print("Метаданные:", metadata)
    
    # Тест копирования
    print("Тест копирования:", await copy_object(test_key, copy_key))
    
    # Тест списка объектов
    print("Список объектов:", len(await list_objects()))
    
    # Тест presigned URL
    print("Presigned URL:", await generate_presigned_url(test_key))
    
    # Тест скачивания
    print("Тест скачивания:", await download_file(test_key, "/async_test.txt"))
    
    # Тест удаления
    print("Удаление оригинала:", await delete_object(test_key))
    print("Существует объект:", await object_exists(test_key))
    print("Удаление копии:", await delete_object(copy_key))
    print("Существует объект:", await object_exists(copy_key))
    
    # Проверка после удаления
    print("всё")

async def main():
    data = await list_objects()
    for item, test in data.items():
        print(await delete_object(item))
        
if __name__ == "__main__":
    asyncio.run(main())