import asyncio
import os

import aiomysql


class MySql:
    def __init__(self):
        self.credentials = dict(
            host=os.environ.get("MYSQL_HOST", "rabbit_ws_mysql"),
            port=os.environ.get("MYSQL_PORT", 3306),
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PASSWORD"],
            db=os.environ["MYSQL_DATABASE"],
            loop=asyncio.get_event_loop()
        )
        self.pool = None

    async def create_pool(self):
        self.pool = await aiomysql.create_pool(**self.credentials)

    async def close_pool(self):
        self.pool.close()
        await self.pool.wait_closed()


mysql = MySql()
