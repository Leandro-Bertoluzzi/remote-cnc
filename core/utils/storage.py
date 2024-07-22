try:
    from ..config import REDIS_HOST, REDIS_PORT, REDIS_DB_STORAGE
except ImportError:
    from config import REDIS_HOST, REDIS_PORT, REDIS_DB_STORAGE
import redis


def add_value_with_id(suffix: str, id: int, value: str):
    key = f'{suffix}:{id}'
    set_value(key, value)


def set_value(key: str, value: str):
    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB_STORAGE
    )
    r.set(key, value)


def get_value_from_id(suffix: str, id: int):
    key = f'{suffix}:{id}'
    return get_value(key)


def get_value(key: str) -> str:
    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB_STORAGE,
        decode_responses=True
    )

    value = r.get(key)
    return str(value) if value is not None else ''


def get_all_values(suffix: str):
    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB_STORAGE,
        decode_responses=True
    )
    response: dict[str, str] = {}

    keys_filter = f'{suffix}:*'
    for key in r.scan_iter(keys_filter):
        value = r.get(key)
        response[key] = str(value) if value is not None else ''
    return response


def delete_value(key: str):
    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB_STORAGE
    )
    r.delete(key)
