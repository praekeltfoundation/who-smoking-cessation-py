import time

from prometheus_client import Counter, Histogram
from sanic import Sanic

RQS_COUNT = Counter(
    "sanic_request_count", "Sanic Request Count", ["method", "endpoint", "http_status"]
)

RQS_LATENCY = Histogram(
    "sanic_request_latency_sec",
    "Sanic Request Latency Histogram",
    ["method", "endpoint", "http_status"],
)


def setup_metrics_middleware(app: Sanic) -> None:
    @app.middleware("request")
    async def before_request(request):
        if request.path != "/metrics" and request.method != "OPTIONS":
            request.ctx.start_time = time.monotonic()

    @app.middleware("response")
    async def before_response(request, response):
        start_time = getattr(request.ctx, "start_time", None)
        if start_time:
            RQS_LATENCY.labels(request.method, request.path, response.status).observe(
                time.monotonic() - request.ctx.start_time
            )
            RQS_COUNT.labels(request.method, request.path, response.status).inc()
