from os import environ

AMQP_URL = environ.get("AMQP_URL", "amqp://guest:guest@127.0.0.1/")
CONCURRENCY = int(environ.get("CONCURRENCY", "20"))
TRANSPORT_NAME = environ.get("TRANSPORT_NAME", "whatsapp")
LOG_LEVEL = environ.get("LOG_LEVEL", "INFO")
REDIS_URL = environ.get("REDIS_URL", "redis://127.0.0.1:6379")
TTL = int(environ.get("TTL", "3600"))
ANSWER_BATCH_SIZE = int(environ.get("ANSWER_BATCH_SIZE", "500"))
ANSWER_BATCH_TIME = int(environ.get("ANSWER_BATCH_TIME", "5"))
ANSWER_API_TOKEN = environ.get("ANSWER_API_TOKEN")
ANSWER_API_URL = environ.get("ANSWER_API_URL")
ANSWER_RESOURCE_ID = environ.get("ANSWER_RESOURCE_ID")
SENTRY_TRACES_SAMPLE_RATE = float(environ.get("SENTRY_TRACES_SAMPLE_RATE", 0.0))
APPLICATION_CLASS = environ.get(
    "APPLICATION_CLASS", "who.smoking_cessation.Application"
)
