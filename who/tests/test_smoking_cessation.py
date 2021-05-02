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
    Under 25 years old should be ineligible
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
async def test_state_gender():
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
    assert u.state.name == "state_gender"
    assert reply.content == "\n".join(
        [
            "⬛⬛⬜⬜⬜",
            "",
            "What gender do you identify as?",
            "",
            "1. Male",
            "2. Female",
            "3. Other",
            "4. Rather not say",
            "5. Skip this question",
        ]
    )

    app = Application(u)
    msg = Message(
        content="3",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.answers["state_gender"] == "other"
    assert u.state.name == "state_smoking_frequency"


@pytest.mark.asyncio
async def test_state_smoking_frequency():
    u = User(
        addr="27820001001",
        state=StateData(name="state_gender"),
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
    assert u.state.name == "state_smoking_frequency"
    assert reply.content == "\n".join(
        [
            "⬛⬛⬛⬜⬜",
            "",
            "How often do you use tobacco?",
            "",
            "1. Daily",
            "2. Weekly",
            "3. Every now and then",
            "4. Only socially",
            "5. Skip this question",
        ]
    )

    app = Application(u)
    msg = Message(
        content="3",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.answers["state_smoking_frequency"] == "now_and_then"
    assert u.state.name == "state_tobacco_type"


@pytest.mark.asyncio
async def test_state_smoking_spend():
    u = User(
        addr="27820001001",
        state=StateData(name="state_tobacco_type"),
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
    assert u.state.name == "state_smoking_spend"
    assert reply.content == "\n".join(
        [
            "⬛⬛⬛⬛⬛⬛⬜",
            "",
            "How much do you spend on tobacco products weekly?",
            "_Only send the amount in numbers_",
            "",
            "Type *SKIP* to move on to the next step in the Quit Challenge.",
        ]
    )

    app = Application(u)
    msg = Message(
        content="R300",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert reply.content == "⚠️ Please enter a valid amount"

    app = Application(u)
    msg = Message(
        content="300",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.answers["state_smoking_spend"] == "300"
    assert u.state.name == "state_quit_reason"


@pytest.mark.asyncio
async def test_state_tobacco_type():
    u = User(
        addr="27820001001",
        state=StateData(name="state_smoking_frequency"),
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
    assert u.answers["state_smoking_frequency"] == "weekly"
    assert u.state.name == "state_tobacco_type"
    assert reply.content == "\n".join(
        [
            "⬛⬛⬛⬛⬜",
            "",
            "What type of tobacco products do you usually use?",
            "",
            "1. Smoked tobacco - _includes cigarettes, cigars, cigarillos, "
            "roll-your-own, shisha (also known as hookah or waterpipe), "
            "kreteks and bidis_",
            "2. Smokeless tobacco - _includes chewing tobacco, snuff, and snus_",
            "3. Heated tobacco products ",
            "4. More than one type of tobacco product",
            "5. Other",
            "6. Skip this question",
        ]
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
    assert u.answers["state_tobacco_type"] == "smokeless"
    assert u.state.name == "state_smoking_spend"


@pytest.mark.asyncio
async def test_state_quit_reason():
    u = User(
        addr="27820001001",
        state=StateData(name="state_smoking_spend"),
        session_id="1",
    )
    app = Application(u)
    msg = Message(
        content="200",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_quit_reason"
    assert reply.content == "\n".join(
        [
            "⬛⬛⬛⬛⬛",
            "",
            "Can you share one reason you're motivated to quit tobacco?",
            "",
            "_Select a number from the list below, or reply with *7* "
            "to type out your own reason_",
            "",
            "1. 🦠 to protect yourself from getting a severe case of COVID-19",
            "2. 👍 to set a good example for your family and friends",
            "3. 💸 to save money",
            "4. 🌳 to protect the environment",
            "5. 🫁 to maintain a healthier body and lifestyle",
            "6. 👶 to reduce health risks of those around you",
            "7. Other ",
            "8. Skip",
        ]
    )

    app = Application(u)
    msg = Message(
        content="3",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.answers["state_quit_reason"] == "save_money"
    assert u.state.name == "state_quit_next"


@pytest.mark.asyncio
async def test_state_quit_next():
    u = User(
        addr="27820001001",
        state=StateData(name="state_quit_reason"),
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
    assert u.state.name == "state_quit_next"
    assert reply.content == "\n".join(
        [
            "*That's great! Try to keep this motivation in mind "
            "throughout your quit journey.* 💪",
            "",
            "Type *NEXT* to move on to the next step in the Quit Challenge.",
            "",
            "1. Next",
        ]
    )

    app = Application(u)
    msg = Message(
        content="next",
        to_addr="27820001002",
        from_addr="27820001001",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
    )
    [reply] = await app.process_message(msg)
    assert u.state.name == "state_age"


@pytest.mark.asyncio
async def test_result():
    u = User(
        addr="27820001001",
        state=StateData(name="state_quit_next"),
        session_id="1",
    )
    app = Application(u)
    msg = Message(
        content="next",
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
