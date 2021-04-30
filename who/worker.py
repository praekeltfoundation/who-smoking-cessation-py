import asyncio
import importlib
import logging
from typing import Callable, List
from urllib.parse import urljoin

import aiohttp
import aioredis
from aio_pika import Connection, ExchangeType, IncomingMessage
from aio_pika import Message as AMQPMessage
from aio_pika import connect_robust
from aio_pika.message import DeliveryMode

from who import config
from who.models import Answer, Event, Message, User
from who.utils import DECODE_MESSAGE_EXCEPTIONS, HTTP_EXCEPTIONS

logging.basicConfig(level=config.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)


class Worker:
    def __init__(self):
        modname, clsname = config.APPLICATION_CLASS.rsplit(".", maxsplit=1)
        module = importlib.import_module(modname)
        self.ApplicationClass = getattr(module, clsname)

    async def setup(self):
        self.connection = await connect_robust(config.AMQP_URL)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=config.CONCURRENCY)
        self.exchange = await self.channel.declare_exchange(
            "vumi", type=ExchangeType.DIRECT, durable=True, auto_delete=False
        )

        self.redis = await aioredis.create_redis_pool(config.REDIS_URL)

        self.inbound_queue = await self.setup_consume(
            f"{config.TRANSPORT_NAME}.inbound", self.process_message
        )
        self.event_queue = await self.setup_consume(
            f"{config.TRANSPORT_NAME}.event", self.process_event
        )

        if (
            config.ANSWER_API_URL
            and config.ANSWER_API_TOKEN
            and config.ANSWER_RESOURCE_ID
        ):
            self.answer_worker = AnswerWorker(self.connection)
            await self.answer_worker.setup()
        else:
            self.answer_worker = None

    async def setup_consume(self, routing_key: str, callback: Callable):
        queue = await self.channel.declare_queue(
            routing_key, durable=True, auto_delete=False
        )
        await queue.bind(self.exchange, routing_key)
        await queue.consume(callback)
        return queue

    async def teardown(self):
        await self.connection.close()
        self.redis.close()
        await self.redis.wait_closed()
        if self.answer_worker:
            await self.answer_worker.teardown()

    async def process_message(self, amqp_msg: IncomingMessage):
        try:
            msg = Message.from_json(amqp_msg.body.decode("utf-8"))
        except DECODE_MESSAGE_EXCEPTIONS:
            logger.exception(f"Invalid message body {amqp_msg.body!r}")
            amqp_msg.reject(requeue=False)
            return

        async with amqp_msg.process(requeue=True):
            logger.debug(f"Processing inbound message {msg}")
            user_data = await self.redis.get(f"user.{msg.from_addr}", encoding="utf-8")
            user = User.get_or_create(msg.from_addr, user_data)
            app = self.ApplicationClass(user)
            for outbound in await app.process_message(msg):
                await self.publish_message(outbound)
            if self.answer_worker:
                for answer in app.answer_events:
                    await self.publish_answer(answer)
            await self.redis.setex(f"user.{msg.from_addr}", config.TTL, user.to_json())

    async def publish_message(self, msg: Message):
        await self.exchange.publish(
            AMQPMessage(
                msg.to_json().encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
                content_encoding="UTF-8",
            ),
            routing_key=f"{config.TRANSPORT_NAME}.outbound",
        )

    async def publish_answer(self, answer: Answer):
        await self.exchange.publish(
            AMQPMessage(
                answer.to_json().encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
                content_encoding="UTF-8",
            ),
            routing_key=f"{config.TRANSPORT_NAME}.answer",
        )

    async def process_event(self, amqp_msg: IncomingMessage):
        try:
            event = Event.from_json(amqp_msg.body.decode("utf-8"))
        except DECODE_MESSAGE_EXCEPTIONS:
            logger.exception(f"Invalid event body {amqp_msg.body!r}")
            amqp_msg.reject(requeue=False)
            return

        async with amqp_msg.process(requeue=True):
            logger.debug(f"Processing event {event}")


class AnswerWorker:
    def __init__(self, connection: Connection):
        self.connection = connection
        self.answers: List[IncomingMessage] = []
        self.session = aiohttp.ClientSession(
            raise_for_status=True,
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(limit=1),
            headers={
                "Authorization": f"Token {config.ANSWER_API_TOKEN}",
                "Content-Type": "application/vnd.api+json",
            },
        )

    async def setup(self):
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=config.ANSWER_BATCH_SIZE)
        self.exchange = await self.channel.declare_exchange(
            "vumi", type=ExchangeType.DIRECT, durable=True, auto_delete=False
        )
        self.answer_queue = await self.setup_consume(
            f"{config.TRANSPORT_NAME}.answer", self.process_answer
        )
        self.periodic_task = asyncio.create_task(self._periodic_loop())

    async def setup_consume(self, routing_key: str, callback: Callable):
        queue = await self.channel.declare_queue(
            routing_key, durable=True, auto_delete=False
        )
        await queue.bind(self.exchange, routing_key)
        await queue.consume(callback)
        return queue

    async def teardown(self):
        self.periodic_task.cancel()
        await self.channel.close()

    async def process_answer(self, amqp_msg: IncomingMessage):
        self.answers.append(amqp_msg)

    async def _periodic_loop(self):
        while True:
            await asyncio.sleep(config.ANSWER_BATCH_TIME)
            await self._push_results()

    async def _push_results(self):
        msgs, self.answers = self.answers, []
        answers = (Answer.from_json(a.body.decode()) for a in msgs)
        answers: List[Answer] = []
        for msg in msgs:
            try:
                answers.append(Answer.from_json(msg.body.decode("utf-8")))
            except DECODE_MESSAGE_EXCEPTIONS:
                logger.exception(f"Invalid answer body {msg.body!r}")
                msg.reject(requeue=False)
        if not answers:
            return
        try:
            await self.session.post(
                url=urljoin(
                    config.ANSWER_API_URL,
                    f"flow-results/packages/{config.ANSWER_RESOURCE_ID}/responses/",
                ),
                json={
                    "data": {
                        "type": "responses",
                        "id": config.ANSWER_RESOURCE_ID,
                        "attributes": {
                            "responses": [
                                [
                                    a.timestamp.isoformat(),
                                    a.row_id,
                                    a.address,
                                    a.session_id,
                                    a.question,
                                    a.response,
                                    a.response_metadata,
                                ]
                                for a in answers
                            ]
                        },
                    }
                },
            )
        except HTTP_EXCEPTIONS:
            logger.exception("Error sending results to flow results server")
            self.answers.extend(msgs)
            return

        for m in msgs:
            m.ack()


if __name__ == "__main__":  # pragma: no cover
    worker = Worker()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker.setup())
    logger.info("Worker running")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(worker.teardown())
