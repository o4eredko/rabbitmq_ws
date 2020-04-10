import os

import jwt
from fastapi import Depends, Cookie
from starlette import status
from starlette.websockets import WebSocket

from app.dataclasses import AuthData
from app.mysql import mysql
from app.rmq import rabbit_mq

from app.logger import get_custom_logger

logger = get_custom_logger(__name__)


def get_mysql():
    return mysql


async def get_mysql_conn(obj: get_mysql = Depends()):
    async with obj.pool.acquire() as connection:
        yield connection


def get_rmq():
    return rabbit_mq


async def get_authorization(websocket: WebSocket, authorization: str = Cookie(None)) -> AuthData:
    try:
        payload = jwt.decode(authorization, os.getenv("SECRET_KEY"))
        return AuthData.from_jwt_payload(payload)
    except (jwt.DecodeError, TypeError) as exc:
        logger.error(str(exc))
        await websocket.close(status.WS_1008_POLICY_VIOLATION)
