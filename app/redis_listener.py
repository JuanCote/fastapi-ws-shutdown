import asyncio

import redis.asyncio as redis

from app.config import REDIS_CHANNEL, REDIS_HOST, REDIS_PORT
from app.ws_manager import ConnectionManager


async def listen_for_broadcasts(manager: ConnectionManager):
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe(REDIS_CHANNEL)

    print(f"🔊 Subscribed to Redis channel: {REDIS_CHANNEL}")

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message:
                await manager.broadcast(message["data"])
            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        print("🛑 Broadcast listener cancelled.")
    finally:
        await pubsub.unsubscribe(REDIS_CHANNEL)
        await pubsub.close()
        await r.close()
        print("✅ Redis pubsub closed")
