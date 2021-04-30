import time

import sentry_sdk
from prometheus_client import CONTENT_TYPE_LATEST
from prometheus_client.exposition import generate_latest
from sanic import Sanic
from sanic.request import Request
from sanic.response import HTTPResponse, json, raw
from sentry_sdk.integrations.sanic import SanicIntegration

from who import config
from who.metrics import setup_metrics_middleware
from who.worker import Worker

sentry_sdk.init(
    integrations=[SanicIntegration()],
    traces_sample_rate=config.SENTRY_TRACES_SAMPLE_RATE,
)

app = Sanic("who")
app.update_config(config)
setup_metrics_middleware(app)


@app.listener("before_server_start")
async def setup_worker(app, loop):
    app.worker = Worker()
    await app.worker.setup()


@app.listener("after_server_stop")
async def shutdown_worker(app, loop):
    await app.worker.teardown()


@app.route("/")
async def health(request: Request) -> HTTPResponse:
    result: dict = {"status": "ok", "amqp": {}, "redis": {}}
    worker: Worker = app.worker  # type: ignore

    if worker.connection.connection is None:  # pragma: no cover
        result["amqp"]["connection"] = False
        result["status"] = "down"
    else:
        result["amqp"]["time_since_last_heartbeat"] = (
            worker.connection.loop.time() - worker.connection.heartbeat_last
        )
        result["amqp"]["connection"] = True

    try:
        start = time.monotonic()
        await worker.redis.ping()
        result["redis"]["response_time"] = time.monotonic() - start
        result["redis"]["connection"] = True
    except ConnectionError:  # pragma: no cover
        result["status"] = "down"
        result["redis"]["connection"] = False

    return json(result, status=200 if result["status"] == "ok" else 500)


@app.route("/metrics")
async def metrics(request: Request) -> HTTPResponse:
    return raw(generate_latest(), content_type=CONTENT_TYPE_LATEST)
