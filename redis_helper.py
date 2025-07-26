# redis_helper.py
import aioredis
from config import REDIS_HOST, REDIS_PORT, REDIS_DB

class RedisHelper:
    def __init__(self):
        self._pool = None

    async def init_pool(self):
        self._pool = await aioredis.create_redis_pool(
            (REDIS_HOST, REDIS_PORT),
            db=REDIS_DB,
            maxsize=10
        )

    async def get(self, key: str):
        return await self._pool.get(key, encoding="utf-8")

    async def set(self, key: str, value: str, expire: int = None):
        await self._pool.set(key, value, expire=expire)

    async def close(self):
        self._pool.close()
        await self._pool.wait_closed()

redis_helper = RedisHelper()
