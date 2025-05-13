from __future__ import annotations

import asyncio
import logging
import sys
from typing import List

from fastapi import WebSocket

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(process)d WS_MANAGER %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ws_manager")


class ConnectionManager:
    def __init__(self) -> None:
        self._active: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def add(self, ws: WebSocket) -> None:
        """Accept and track a new WebSocket connection."""
        await ws.accept()
        async with self._lock:
            self._active.append(ws)
            if ws.client is not None:
                logger.info(
                    "WS connected %s:%s (total=%d)",
                    ws.client.host,
                    ws.client.port,
                    len(self._active),
                )
            else:
                logger.info(
                    "WS connected (unknown client) (total=%d)", len(self._active)
                )

    def remove(self, ws: WebSocket) -> None:
        """Remove a disconnected WebSocket from the active list."""
        if ws in self._active:
            self._active.remove(ws)
            if ws.client is not None:
                logger.info(
                    "WS disconnected %s:%s (total=%d)",
                    ws.client.host,
                    ws.client.port,
                    len(self._active),
                )
            else:
                logger.info(
                    "WS disconnected (unknown client) (total=%d)", len(self._active)
                )

    async def broadcast(self, message: str) -> None:
        """Send a message to all active WebSocket clients."""
        for ws in list(self._active):
            try:
                await ws.send_text(message)
            except Exception as exc:
                if ws.client is not None:
                    logger.warning(
                        "Error sending to WS %s:%s → removing (%s)",
                        ws.client.host,
                        ws.client.port,
                        exc,
                    )
                else:
                    logger.warning(
                        "Error sending to WS (unknown client) → removing (%s)", exc
                    )
                self.remove(ws)

    def active_count(self) -> int:
        """Return the number of currently connected WebSocket clients."""
        return len(self._active)
