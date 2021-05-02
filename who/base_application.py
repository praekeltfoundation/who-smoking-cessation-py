from typing import Any, List, Optional

from prometheus_client import Counter

from who.models import Answer, Message, User
from who.utils import random_id

STATE_CHANGE = Counter(
    "state_change", "Whenever a user's state gets changed", ("from_state", "to_state")
)


class BaseApplication:
    START_STATE = "state_start"

    def __init__(self, user: User):
        self.user = user
        self.answer_events: List[Answer] = []
        self.messages: List[Message] = []
        self.inbound: Optional[Message] = None

    async def get_current_state(self):
        if not self.state_name:
            self.state_name = self.START_STATE
        state_func = getattr(self, self.state_name)
        return await state_func()

    async def go_to_state(self, name):
        """
        Go to another state and have it process the user message instead
        """
        self.state_name = name
        return await self.get_current_state()

    @property
    def state_name(self):
        return self.user.state.name

    @state_name.setter
    def state_name(self, state):
        STATE_CHANGE.labels(self.state_name, state).inc()
        self.user.state.name = state

    async def process_message(self, message: Message) -> List[Message]:
        """
        Processes the message, and returns a list of messages to return to the user
        """
        self.inbound = message
        if message.content == "!reset":
            self.state_name = self.START_STATE
            self.user.answers = {}
            self.user.session_id = None
        state = await self.get_current_state()
        if (
            message.session_event == Message.SESSION_EVENT.NEW
            or self.user.session_id is None
        ):
            self.user.session_id = random_id()
            await state.display(message)
        else:
            await state.process_message(message)
        return self.messages

    def save_answer(self, name: str, value: Any):
        """
        Saves an answer from the user
        """
        self.user.answers[name] = value
        self.answer_events.append(
            Answer(
                question=name,
                response=value,
                address=self.user.addr,
                session_id=self.user.session_id or random_id(),
            )
        )

    def send_message(self, content, continue_session=True, **kw):
        """
        Sends a reply to the user
        """
        self.messages.append(self.inbound.reply(content, continue_session, **kw))
