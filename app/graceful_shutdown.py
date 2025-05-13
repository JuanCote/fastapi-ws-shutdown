import asyncio
import os
import signal
from datetime import datetime, timedelta

import redis.asyncio as redis

from app.config import REDIS_HOST, REDIS_PORT
from app.ws_manager import ConnectionManager

REDIS_SHUTDOWN_KEY = f"shutdown:{os.getpid()}"
SHUTDOWN_TIMEOUT = 60 * 30  # 30 minutes

shutdown_event: asyncio.Event = asyncio.Event()


def setup_signal_handlers(manager: ConnectionManager) -> None:
    """Install SIGINT/SIGTERM handlers and trigger graceful shutdown."""
    loop = asyncio.get_running_loop()

    def handle_shutdown_signal():
        print("⚠️  Shutdown signal received.")
        shutdown_event.set()
        loop.create_task(wait_for_ws_shutdown(manager))

    loop.add_signal_handler(signal.SIGINT, handle_shutdown_signal)
    loop.add_signal_handler(signal.SIGTERM, handle_shutdown_signal)


def is_shutting_down() -> bool:
    """Return True if shutdown was triggered."""
    return shutdown_event.is_set()


async def wait_for_ws_shutdown(manager: ConnectionManager) -> None:
    """Wait until all WebSocket clients disconnect or timeout expires."""
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    deadline = datetime.now() + timedelta(seconds=SHUTDOWN_TIMEOUT)

    print("🛑 Graceful shutdown in progress...")
    try:
        while datetime.now() < deadline:
            count = manager.active_count()
            await r.set(REDIS_SHUTDOWN_KEY, str(count), ex=60)

            if count == 0:
                print("✅ All WebSocket clients disconnected. Shutting down.")
                return

            remaining = (deadline - datetime.now()).total_seconds()
            print(f"⏳ {count} clients still connected – {int(remaining)}s left")
            await asyncio.sleep(5)

        print("⏱ Timeout expired. Forcing shutdown.")
    finally:
        await r.delete(REDIS_SHUTDOWN_KEY)
        await r.close()
        os._exit(0)  # Forcefully terminate the process
