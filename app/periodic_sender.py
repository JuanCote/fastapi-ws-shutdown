import asyncio

import redis.asyncio as redis

from .config import REDIS_CHANNEL, REDIS_HOST, REDIS_PORT

LOCK_KEY = "periodic_broadcast_lock"
LOCK_EXPIRE = 9  # Lock timeout in seconds


async def periodic_broadcast() -> None:
    """Periodically publish a test message to Redis if lock acquired."""
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    try:
        while True:
            lock_acquired = await r.set(LOCK_KEY, "1", ex=LOCK_EXPIRE, nx=True)
            if lock_acquired:
                await r.publish(REDIS_CHANNEL, "🛰 Test notification")
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        print("📴 Periodic sender cancelled.")
    finally:
        await r.close()
