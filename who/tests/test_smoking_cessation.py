import pytest

from who.models import Message, StateData, User
from who.smoking_cessation import Application


@pytest.mark.asyncio
async def test_new_user():
    """
    New users should be put in the start state
    """
    u = User.get_or_create("27820001001", "")
    assert u.state.name is None
    assert u.session_id is None
    app = Application(u)
    msg = Message(
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert reply.content == "\n".join(
        [
            "Let's get started!",
            ""
            "We have 5 short questions to find out more about you and your "
            "tobacco use habits. After that we'll help you choose your "
            "quit date 🚬 ",
            "",
            "⬛⬜⬜⬜⬜",
            "",
            "How old are you?",
            "",
            "1. Under 25",
            "2. 25-35",
            "3. 35-45",
            "4. 45-55",
            "5. 55+",
            "6. Skip this question",
        ]
    )
    assert u.state.name == "state_age"
    assert u.session_id is not None


@pytest.mark.asyncio
async def test_returning_user():
    """
    Returning user messages should be treated as responses to their current state
    """
    u = User(addr="27820001001", state=StateData(name="state_age"), session_id="1")
    app = Application(u)
    msg = Message(
        content="9",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert reply.content == "\n".join(
        [
            "⚠️ This service works best when you use the numbered options available",
            "",
            "Please confirm how old you are.",
            "1. Under 25",
            "2. 25-35",
            "3. 35-45",
            "4. 45-55",
            "5. 55+",
            "6. Skip this question",
        ]
    )
    assert u.state.name == "state_age"
    assert u.session_id == "1"


@pytest.mark.asyncio
async def test_result_ineligible():
    """
    Under 18 years old should be ineligible
    """
    u = User(addr="27820001001", state=StateData(name="state_age"), session_id="1")
    app = Application(u)
    msg = Message(
        content="1",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert reply.content == "\n".join(
        [
            "Based on your age you are currently NOT able to participate in "
            "the QUIT challenge. ",
            "",
            "___",
            "",
            "Reply :",
            "*32* to return to our tobacco content",
            "📌  *0* for the WHO main *MENU*,",
        ]
    )
    assert u.session_id is None
    assert u.state.name == "state_age"


@pytest.mark.asyncio
async def test_result():
    """
    Health Care Workers should be in phase 1
    """
    u = User(
        addr="27820001001",
        state=StateData(name="state_age"),
        session_id="1",
    )
    app = Application(u)
    msg = Message(
        content="2",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert reply.content == "\n".join(
        [
            "That's it for now - well done!",
            "",
            "The countdown begins! 🎉 We are here to help you prepare & "
            "follow through. Get ready!",
            "",
            "Over the next few days, you will receive tips to help you prepare "
            "for your quit date.",
            "",
            "Additional support is available to you 24/7. Why not check out "
            "our list of 100 reasons"
            " to quit tobacco:  "
            "https://who.medium.com/more-than-100-reasons-"
            "to-quit-tobacco-e2c4060e64e8 ",
            "",
            "Reply with a word in bold (or emoji) at any time to "
            "get more information:",
            "",
            "*Motivation* 💪",
            "*Cravings* 👿",
            "*Triggers* 🗯️",
            "",
            "___",
            "",
            "Reply :",
            "*32* to return to our tobacco content",
            "📌  *0* for the WHO main *MENU*,",
        ]
    )
    assert u.state.name == "state_age"
