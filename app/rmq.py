import asyncio
import os
import time
from contextlib import asynccontextmanager
from typing import List, Awaitable, Callable

import aiormq

from app.dataclasses import ExchangeData
from app.utils import get_fanout_names

FANOUT_EXCHANGE_NAME = "test-fanout"
QUEUE_NAME = "ws_q"


class RabbitMQConnector:
    def __init__(self):
        self.connection: aiormq.connection = None

    @staticmethod
    def _conn_url() -> str:
        username = os.getenv('RABBITMQ_DEFAULT_USER')
        password = os.getenv('RABBITMQ_DEFAULT_PASS')
        host = os.getenv('RABBITMQ_DEFAULT_HOST')
        return f"amqp://{username}:{password}@{host}/"

    async def _wait_for_connection(self) -> aiormq.connection:
        conn_url = self._conn_url()
        while True:
            try:
                return await aiormq.connect(conn_url)
            except ConnectionError:
                await asyncio.sleep(.5)

    async def connect(self):
        self.connection = await self._wait_for_connection()
        return self.connection

    async def close(self):
        await self.connection.close()


class RabbitMQ:
    def __init__(self):
        self.conn = RabbitMQConnector()
        self.common_fanouts: List[ExchangeData] = []
        self.queue_names = ("rabbit_ws-receive", "server-send", "rabbit_ws-send")
        self.queues = {}

    @property
    @asynccontextmanager
    async def channel_ctx(self):
        channel = await self.conn.connection.channel()
        try:
            yield channel
        finally:
            await channel.close()

    @property
    def connection(self):
        return self.conn.connection

    async def _load_fanouts(self):
        async for fanout_name in get_fanout_names():
            exchange = ExchangeData(name=fanout_name)
            self.common_fanouts.append(exchange)

    async def _declare_exchanges(self):
        async with self.channel_ctx as channel:
            for exchange in self.common_fanouts:
                await channel.exchange_declare(exchange=exchange.name, exchange_type=exchange.type)
            for queue in self.queue_names:
                declare_ok = await channel.queue_declare(queue=queue)
                self.queues[queue] = declare_ok.queue

    async def startup(self):
        await self.conn.connect()
        # await self._load_fanouts()
        await self._declare_exchanges()

    async def shutdown(self):
        await self.conn.close()


rabbit_mq = RabbitMQ()


class RabbitMQClient:
    def __init__(self, client_id: str, rabbit_mq: RabbitMQ,
                 on_message_callback: Callable[[aiormq.types.DeliveredMessage], Awaitable]):
        self.client_id = client_id
        self.rabbit_mq = rabbit_mq
        self.on_msg_cb = on_message_callback
        self.channel = None
        self.queues = {"rabbit_ws-receive": self.rabbit_mq.queues["rabbit_ws-receive"]}

    async def get_own_topic(self) -> ExchangeData:
        assert self.client_id
        topic = ExchangeData(name=f"{self.client_id}-receive", type="topic", routing_key="*")
        await self.channel.exchange_declare(exchange=topic.name, exchange_type=topic.type)
        return topic

    async def get_exchanges_to_subscribe(self) -> List[ExchangeData]:
        return [await self.get_own_topic(), *self.rabbit_mq.common_fanouts]

    async def _on_message_callback_wrapper(self, msg: aiormq.types.DeliveredMessage):
        await msg.channel.basic_ack(msg.delivery.delivery_tag)
        await self.on_msg_cb(msg)

    async def _bind_queue(self, exchange):
        await self.channel.queue_bind(
            queue=self.queues[self.client_id],
            exchange=exchange.name,
            routing_key=exchange.routing_key
        )

    async def _setup(self, channel: aiormq.channel):
        self.channel = channel
        declare_ok = await channel.queue_declare(queue=f"{self.client_id}{time.time()}")
        self.queues[self.client_id] = declare_ok.queue

        queue_bindings = (
            self._bind_queue(exchange) for exchange in await self.get_exchanges_to_subscribe())
        await asyncio.gather(*queue_bindings)

        for queue in self.queues.values():
            await channel.basic_consume(queue, self._on_message_callback_wrapper)

    async def _teardown(self):
        for exchange in await self.get_exchanges_to_subscribe():
            await self.channel.queue_unbind(
                queue=self.queues[self.client_id], exchange=exchange.name,
                routing_key=exchange.routing_key
            )
        await self.channel.queue_delete(queue=self.queues[self.client_id])
        self.channel = None

    async def _publisher(self, msg: str, routing_key=None):
        await self.channel.basic_publish(body=msg.encode(), exchange='', routing_key=routing_key)

    @property
    @asynccontextmanager
    async def publish_ctx(self):
        async with self.rabbit_mq.channel_ctx as channel:
            await self._setup(channel)
            try:
                yield self._publisher
            finally:
                await self._teardown()
