from functools import partial

from fastapi import APIRouter, Depends
from starlette import status

from starlette.websockets import WebSocket, WebSocketState

from app.dependencies import get_authorization, get_rmq
from app.rmq import RabbitMQClient
from app.utils import on_message
from app.logger import get_custom_logger

router = APIRouter()
logger = get_custom_logger(__name__)


@router.websocket("/ws")
async def ws_client_endpoint(
        websocket: WebSocket,
        auth: get_authorization = Depends(),
        rabbit_mq: get_rmq = Depends()
):
    logger.info(auth)
    await websocket.accept()
    client = RabbitMQClient(auth.email, rabbit_mq, partial(on_message, websocket=websocket))
    async with client.publish_ctx as publisher:
        while True:
            try:
                if websocket.client_state == WebSocketState.DISCONNECTED:
                    break
                json = await websocket.receive_json()
                for msg in json:
                    try:
                        await publisher(**msg)
                    except TypeError:
                        logger.error(f"Invalid JSON schema: {msg}")
            except Exception as exc:
                logger.error(f"Error occurred in WS endpoint. {exc}")
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        logger.info(f"User {auth.email} disconnected from ws")
