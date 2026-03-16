import redis

from core.config import REDIS_DB_STORAGE, REDIS_HOST, REDIS_PORT

# Shared connection pool – avoids creating a new TCP connection per operation
_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_STORAGE)


def _get_redis(*, decode: bool = False) -> redis.Redis:
    return redis.Redis(connection_pool=_pool, decode_responses=decode)


def add_value_with_id(suffix: str, id: int, value: str):
    key = f"{suffix}:{id}"
    set_value(key, value)


def set_value(key: str, value: str):
    r = _get_redis()
    r.set(key, value)


def get_value_from_id(suffix: str, id: int):
    key = f"{suffix}:{id}"
    return get_value(key)


def get_value(key: str) -> str:
    r = _get_redis(decode=True)
    value = r.get(key)
    return str(value) if value is not None else ""


def get_all_values(suffix: str):
    r = _get_redis(decode=True)
    response: dict[str, str] = {}

    keys_filter = f"{suffix}:*"
    for key in r.scan_iter(keys_filter):
        value = r.get(key)
        response[key] = str(value) if value is not None else ""
    return response


def delete_value(key: str):
    r = _get_redis()
    r.delete(key)
