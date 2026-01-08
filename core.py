from functools import wraps
from datetime import datetime, timedelta
import pytz, threading
import asyncio, time

from create_bot import moscow_tz

def time_now() -> datetime:
    return datetime.now(pytz.UTC)

def strftime(_datetime: datetime) -> str:
    return _datetime.strftime("%Y-%m-%d")


def strptime(str_datetime: str) -> datetime:
    return datetime.strptime(str_datetime, "%Y-%m-%d")


def is_hashable(obj):
    """Проверяет, является ли объект хешируемым."""
    try:
        hash(obj)
        return True
    except TypeError:
        return False

def cache_with_expiration(expiration_seconds: int):
    def decorator(func):
        cache = {}
        async_lock = None  # Ленивая инициализация асинхронного лока
        sync_lock = threading.Lock()

        def get_cache_key(*args, **kwargs):
            filtered_args = [arg for arg in args if is_hashable(arg)]
            filtered_kwargs = {k: v for k, v in kwargs.items() if is_hashable(v)}
            return (tuple(filtered_args), frozenset(filtered_kwargs.items()))

        @wraps(func)
        async def async_wrapped(*args, **kwargs):
            nonlocal async_lock
            if async_lock is None:
                async_lock = asyncio.Lock()  # Создаем лок в текущем event loop
            async with async_lock:
                now = time.time()
                key = get_cache_key(*args, **kwargs)
                if key in cache:
                    result, timestamp = cache[key]
                    if now - timestamp < expiration_seconds:
                        return result
                result = await func(*args, **kwargs)
                cache[key] = (result, now)
                return result

        @wraps(func)
        def sync_wrapped(*args, **kwargs):
            with sync_lock:
                now = time.time()
                key = get_cache_key(*args, **kwargs)
                if key in cache:
                    result, timestamp = cache[key]
                    if now - timestamp < expiration_seconds:
                        return result
                result = func(*args, **kwargs)
                cache[key] = (result, now)
                return result

        return async_wrapped if asyncio.iscoroutinefunction(func) else sync_wrapped

    return decorator


def get_mime_type(file_path: str) -> str:
    extension = file_path.lower().split('.')[-1]
    mime_types = {'pdf': 'application/pdf', 'zip': 'application/zip'}

    return mime_types.get(extension, 'application/octet-stream')



def declension(value, cases):
    """
    Склонение слова в зависимости от количества.
    cases: список из трёх форм: [множественное число, единственное число, родительный падеж]
    """
    if 11 <= value % 100 <= 19:
        return cases[0]  # множественное число
    else:
        if value % 10 == 1:
            return cases[1]  # единственное число
        elif value % 10 in (2, 3, 4):
            return cases[2]  # родительный падеж
        else:
            return cases[0]  # множественное число

def time_passed_since(target_date):
    # Получаем текущее время в Москве
    now = datetime.now(moscow_tz)
    
    # Преобразуем переданную дату в московский часовой пояс
    if target_date.tzinfo is None:
        target_date = moscow_tz.localize(target_date)

    # Вычисляем разницу между текущей датой и переданной
    delta = now - target_date
    
    # Получаем общее количество секунд
    total_seconds = int(delta.total_seconds())
    
    # Вычисляем количество месяцев, дней, часов, минут и секунд
    seconds_in_day = 86400
    seconds_in_month = 2592000  # Приблизительно 30 дней

    months = total_seconds // seconds_in_month
    total_seconds %= seconds_in_month
    
    days = total_seconds // seconds_in_day
    total_seconds %= seconds_in_day

    # Форматируем результат
    parts = []
    if months > 0:
        parts.append(f"{months} {declension(months, ['месяцев', 'месяц', 'месяца'])}")
    if days > 0:
        parts.append(f"{days} {declension(days, ['дней', 'день', 'дня'])}")
    return ' и '.join(parts)