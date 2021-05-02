import json
from datetime import date, datetime, timezone

from who.models import Answer, Event, Message, StateData, User


def test_message_serialisation():
    """
    Message should be able to be serialised and deserialised with no changes
    """
    message = Message(
        to_addr="27820001001",
        from_addr="27820001002",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        in_reply_to="original-message-id",
        session_event=Message.SESSION_EVENT.NEW,
        content="message content",
        to_addr_type=Message.ADDRESS_TYPE.MSISDN,
        from_addr_type=Message.ADDRESS_TYPE.MSISDN,
    )
    assert message == Message.from_json(message.to_json())


def test_message_reply():
    """
    Should create a reply message from the original message
    """
    message = Message(
        to_addr="27820001001",
        from_addr="27820001002",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    reply = message.reply("test reply")
    assert reply.to_addr == "27820001002"
    assert reply.from_addr == "27820001001"
    assert reply.content == "test reply"
    assert reply.in_reply_to == message.message_id


def test_message_reply_override():
    """
    Some fields may not be overridden
    """
    message = Message(
        to_addr="27820001001",
        from_addr="27820001002",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    error = None
    try:
        message.reply("test reply", to_addr="invalid")
    except TypeError as e:
        error = e
    assert error is not None


def test_event_serialization():
    """
    Event should be able to be serialised and deserialised with no changes
    """
    event = Event(
        user_message_id="message-id",
        event_type=Event.EVENT_TYPE.DELIVERY_REPORT,
        delivery_status=Event.DELIVERY_STATUS.DELIVERED,
    )
    assert event == Event.from_json(event.to_json())


def test_event_ack():
    """
    sent_message_id should be required for an ack
    """
    exception = None
    try:
        Event(user_message_id="message-id", event_type=Event.EVENT_TYPE.ACK)
    except AssertionError as e:
        exception = e
    assert exception is not None

    Event(
        user_message_id="message-id",
        event_type=Event.EVENT_TYPE.ACK,
        sent_message_id="message-id",
    )


def test_event_nack():
    """
    nack_reason should be required for a nack
    """
    exception = None
    try:
        Event(user_message_id="message-id", event_type=Event.EVENT_TYPE.NACK)
    except AssertionError as e:
        exception = e
    assert exception is not None

    Event(
        user_message_id="message-id",
        event_type=Event.EVENT_TYPE.NACK,
        nack_reason="cannot reach service",
    )


def test_event_delivery_report():
    """
    delivery_status should be required for a delivery report
    """
    exception = None
    try:
        Event(user_message_id="message-id", event_type=Event.EVENT_TYPE.DELIVERY_REPORT)
    except AssertionError as e:
        exception = e
    assert exception is not None

    Event(
        user_message_id="message-id",
        event_type=Event.EVENT_TYPE.DELIVERY_REPORT,
        delivery_status=Event.DELIVERY_STATUS.DELIVERED,
    )


def test_user_serialization():
    """
    Users should be able to be serialised and deserialised with no changes
    """
    user = User("27820001001", state=StateData("state_start"))
    assert user == User.from_json(user.to_json())


def test_user_get_or_create():
    """
    If the data is valid, then return a user with that data, otherwise return a new user
    """
    user = User.get_or_create(
        "27820001001",
        json.dumps({"addr": "27820001001", "state": {"name": "state_start"}}),
    )
    assert user == User("27820001001", state=StateData("state_start"))

    user = User.get_or_create("27820001001", "")
    assert user == User("27820001001")


def test_answer_serialization():
    """
    Answers should be serialised and deserialised with no changes
    """
    answer = Answer(
        question="state_start", response="1", address="27820001001", session_id="1"
    )
    assert answer == Answer.from_json(answer.to_json())

    answer = Answer(
        question="state_start",
        response=datetime.now(tz=timezone.utc),
        address="27820001001",
        session_id="1",
    )
    assert answer == Answer.from_json(answer.to_json())

    answer = Answer(
        question="state_start",
        response=date.today(),
        address="27820001001",
        session_id="1",
    )
    assert answer == Answer.from_json(answer.to_json())

    answer = Answer(
        question="state_start",
        response=datetime.now().time(),
        address="27820001001",
        session_id="1",
    )
    assert answer == Answer.from_json(answer.to_json())
