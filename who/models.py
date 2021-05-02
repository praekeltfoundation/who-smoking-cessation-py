import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timezone
from enum import Enum
from json import JSONDecodeError
from typing import List, Optional, Union

from who.utils import current_timestamp, random_id

VUMI_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
_VUMI_DATE_FORMAT_NO_MICROSECONDS = "%Y-%m-%d %H:%M:%S"


def format_timestamp(timestamp: datetime) -> str:
    return timestamp.strftime(VUMI_DATE_FORMAT)


def date_time_decoder(json_object: dict) -> dict:
    for key, value in json_object.items():
        try:
            date_format = VUMI_DATE_FORMAT
            if "." not in value[-10:]:
                date_format = _VUMI_DATE_FORMAT_NO_MICROSECONDS
            timestamp = datetime.strptime(value, date_format)
            timestamp = timestamp.replace(tzinfo=timezone.utc)
            json_object[key] = timestamp
        except (ValueError, TypeError):
            continue
    return json_object


@dataclass
class Message:
    class SESSION_EVENT(Enum):
        NONE = None
        NEW = "new"
        RESUME = "resume"
        CLOSE = "close"

    class TRANSPORT_TYPE(Enum):
        HTTP_API = "http_api"
        USSD = "ussd"

    class ADDRESS_TYPE(Enum):
        MSISDN = "msisdn"

    to_addr: str
    from_addr: str
    transport_name: str
    transport_type: TRANSPORT_TYPE
    message_version: str = "20110921"
    message_type: str = "user_message"
    timestamp: datetime = field(default_factory=current_timestamp)
    routing_metadata: dict = field(default_factory=dict)
    helper_metadata: dict = field(default_factory=dict)
    message_id: str = field(default_factory=random_id)
    in_reply_to: Optional[str] = None
    provider: Optional[str] = None
    session_event: SESSION_EVENT = SESSION_EVENT.NONE
    content: Optional[str] = None
    transport_metadata: dict = field(default_factory=dict)
    group: Optional[str] = None
    to_addr_type: Optional[ADDRESS_TYPE] = None
    from_addr_type: Optional[ADDRESS_TYPE] = None

    def to_json(self) -> str:
        """
        Converts the message to JSON representation for serialisation over the message
        broker
        """
        data = asdict(self)
        data["timestamp"] = format_timestamp(data["timestamp"])
        data["transport_type"] = data["transport_type"].value
        data["session_event"] = data["session_event"].value
        if data.get("to_addr_type"):
            data["to_addr_type"] = data["to_addr_type"].value
        if data.get("from_addr_type"):
            data["from_addr_type"] = data["from_addr_type"].value
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_string: str):
        """
        Takes a serialised message from the message broker, and converts into a message
        object
        """
        data = json.loads(json_string)
        data = date_time_decoder(data)
        data["transport_type"] = cls.TRANSPORT_TYPE(data["transport_type"])
        data["session_event"] = cls.SESSION_EVENT(data["session_event"])
        if data.get("to_addr_type"):
            data["to_addr_type"] = cls.ADDRESS_TYPE(data["to_addr_type"])
        if data.get("from_addr_type"):
            data["from_addr_type"] = cls.ADDRESS_TYPE(data["from_addr_type"])
        return cls(**data)

    def reply(self, content, continue_session=True, **kw):
        """
        Returns a new Message that's a reply to this message
        """
        for f in [
            "to_addr",
            "from_addr",
            "group",
            "in_reply_to",
            "provider",
            "transport_name",
            "transport_type",
            "transport_metadata",
        ]:
            if f in kw:
                raise TypeError(f"{f} my not be overridden")
        fields = {
            "session_event": Message.SESSION_EVENT.NONE
            if continue_session
            else Message.SESSION_EVENT.CLOSE,
            "to_addr": self.from_addr,
            "from_addr": self.to_addr,
            "group": self.group,
            "in_reply_to": self.message_id,
            "provider": self.provider,
            "transport_name": self.transport_name,
            "transport_type": self.transport_type,
            "transport_metadata": self.transport_metadata,
        }
        fields.update(kw)

        return Message(content=content, **fields)


@dataclass
class Event:
    class DELIVERY_STATUS(Enum):
        PENDING = "pending"
        FAILED = "failed"
        DELIVERED = "delivered"

    class EVENT_TYPE(Enum):
        ACK = "ack"
        NACK = "nack"
        DELIVERY_REPORT = "delivery_report"

    user_message_id: str
    event_type: EVENT_TYPE
    event_id: str = field(default_factory=random_id)
    message_type: str = "event"
    message_version: str = "20110921"
    timestamp: datetime = field(default_factory=current_timestamp)
    routing_metadata: dict = field(default_factory=dict)
    helper_metadata: dict = field(default_factory=dict)
    sent_message_id: Optional[str] = None
    nack_reason: Optional[str] = None
    delivery_status: Optional[DELIVERY_STATUS] = None
    transport_name: Optional[str] = None
    transport_metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.event_type == self.EVENT_TYPE.ACK:
            assert self.sent_message_id is not None
        elif self.event_type == self.EVENT_TYPE.NACK:
            assert self.nack_reason is not None
        elif self.event_type == self.EVENT_TYPE.DELIVERY_REPORT:
            assert self.delivery_status is not None

    def to_json(self) -> str:
        """
        Converts the event to JSON representation for serialisation over the message
        broker
        """
        data = asdict(self)
        data["timestamp"] = format_timestamp(data["timestamp"])
        data["event_type"] = data["event_type"].value
        if data.get("delivery_status"):
            data["delivery_status"] = data["delivery_status"].value
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_string: str):
        """
        Takes a serialised event from the message broker, and converts into an event
        object
        """
        data = json.loads(json_string)
        data = date_time_decoder(data)
        data["event_type"] = cls.EVENT_TYPE(data["event_type"])
        if data.get("delivery_status"):
            data["delivery_status"] = cls.DELIVERY_STATUS(data["delivery_status"])
        return cls(**data)


@dataclass
class StateData:
    name: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class User:
    addr: str
    lang: Optional[str] = None
    answers: dict = field(default_factory=dict)
    state: StateData = field(default_factory=StateData)
    metadata: dict = field(default_factory=dict)
    session_id: Optional[Union[str, int]] = None

    def to_json(self) -> str:
        """
        Converts the user data to JSON representation for storing in the store
        """
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_string: str):
        data = json.loads(json_string)
        data["state"] = StateData(**data["state"])
        return cls(**data)

    @classmethod
    def get_or_create(cls, address: str, json_string: str):
        """
        Either returns a user from the given data, or if the data is invalid or None,
        returns a new user
        """
        try:
            return cls.from_json(json_string)
        except (UnicodeDecodeError, JSONDecodeError, TypeError, KeyError, ValueError):
            return cls(address)


@dataclass
class Answer:
    question: str
    response: Union[str, int, List[str], float, List[float], datetime, date, time]
    address: Union[str, int]
    session_id: Union[str, int]
    timestamp: datetime = field(default_factory=current_timestamp)
    row_id: Union[str, int] = field(default_factory=random_id)
    response_metadata: dict = field(default_factory=dict)

    def to_json(self) -> str:
        """
        Converts the user data to JSON representation for storing in the store
        """
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        if isinstance(self.response, datetime):
            data["response"] = {"_datetime": self.response.isoformat()}
        elif isinstance(self.response, date):
            data["response"] = {"_date": self.response.isoformat()}
        elif isinstance(self.response, time):
            data["response"] = {"_time": self.response.isoformat()}

        return json.dumps(data)

    @classmethod
    def from_json(cls, json_string: str):
        data = json.loads(json_string)
        if isinstance(data["response"], dict):
            if "_datetime" in data["response"]:
                data["response"] = datetime.fromisoformat(data["response"]["_datetime"])
            elif "_date" in data["response"]:
                data["response"] = date.fromisoformat(data["response"]["_date"])
            elif "_time" in data["response"]:
                data["response"] = time.fromisoformat(data["response"]["_time"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)
