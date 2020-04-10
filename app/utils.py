import os

import aiormq
from starlette.websockets import WebSocket, WebSocketState

from app.logger import get_custom_logger
from app.mysql import mysql

logger = get_custom_logger(__name__)


async def get_fanout_names():
    db_name = os.getenv("MYSQL_DATABASE")
    async with mysql.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(f"SELECT currency_key_lr FROM {db_name}.__currency")
            while True:
                row = await cur.fetchone()
                if row is None: break
                yield row[0]


async def on_message(msg: aiormq.types.DeliveredMessage, websocket: WebSocket):
    logger.debug(f"[Client] Received from RMQ: {msg}")
    if websocket.client_state == WebSocketState.CONNECTED:
        await websocket.send_json({
            "exchange": msg.delivery.exchange,
            "routing_key": msg.delivery.routing_key,
            "message": msg.body.decode()
        })
        logger.debug(f"[Client] sent to WS successfully.")
