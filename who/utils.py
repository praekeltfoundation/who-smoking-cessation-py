import asyncio
from datetime import datetime, timezone
from json import JSONDecodeError
from uuid import uuid4

import aiohttp

DECODE_MESSAGE_EXCEPTIONS = (
    UnicodeDecodeError,
    JSONDecodeError,
    TypeError,
    KeyError,
    ValueError,
)

HTTP_EXCEPTIONS = (aiohttp.ClientError, asyncio.TimeoutError)


def random_id():
    return uuid4().hex


def current_timestamp():
    return datetime.now(timezone.utc)


def get_display_choices(choices) -> str:
    return "\n".join(f"{i + 1}. {c.label}" for i, c in enumerate(choices))
