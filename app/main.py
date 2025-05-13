import asyncio
import logging
import sys
from contextlib import asynccontextmanager

import redis.asyncio as redis
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.config import REDIS_CHANNEL, REDIS_HOST, REDIS_PORT
from app.graceful_shutdown import (
    is_shutting_down,
    setup_signal_handlers,
    shutdown_event,
)
from app.periodic_sender import periodic_broadcast
from app.redis_listener import listen_for_broadcasts
from app.ws_manager import ConnectionManager

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(process)d APP_MAIN %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("app.main")

manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan and background tasks."""
    setup_signal_handlers(manager)

    broadcast_task = asyncio.create_task(listen_for_broadcasts(manager))
    periodic_task = asyncio.create_task(periodic_broadcast())

    try:
        yield
    finally:
        for task in (broadcast_task, periodic_task):
            task.cancel()
        await asyncio.gather(broadcast_task, periodic_task, return_exceptions=True)


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.add(ws)

    try:
        redis_conn = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
        )
        await redis_conn.ping()

        while True:
            msg = await ws.receive_text()
            await redis_conn.publish(REDIS_CHANNEL, msg)

    except WebSocketDisconnect:
        if is_shutting_down():
            print("🛑 Graceful shutdown: keeping connection alive until completed.")
            await shutdown_event.wait()
        manager.remove(ws)

    finally:
        if redis_conn:
            await redis_conn.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Disable in production
    )
