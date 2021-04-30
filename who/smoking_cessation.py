from typing import List

from who.base_application import BaseApplication
from who.models import Message
from who.states import Choice, ChoiceState, EndState


class Application(BaseApplication):
    START_STATE = "state_age"

    async def process_message(self, message: Message) -> List[Message]:
        if message.session_event == Message.SESSION_EVENT.CLOSE:
            self.state_name = "state_timeout"
        return await super().process_message(message)

    async def state_timeout(self):
        return EndState(
            self,
            text="\n".join(
                [
                    "We're sorry, but you've taken too long to reply and your "
                    "session has expired.",
                    "If you would like to continue, you can at anytime by "
                    "typing the word *QUIT*.",
                    "",
                    "Reply :",
                    "*32* to return to our tobacco content"
                    "📌  *0* for the WHO main *MENU*",
                ]
            ),
        )

    async def state_age(self):
        async def next_state(choice: Choice):
            if choice.value not in ["25_35", "35_45", "35_45", "45_55", "55+"]:
                return "state_result_ineligible"
            return "state_end"

        return ChoiceState(
            self,
            question="\n".join(
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
                    ""
                ]
            ),
            error="\n".join(
                [
                    "⚠️ This service works best when you use the numbered options "
                    "available",
                    "",
                    "Please confirm how old you are.",
                ]
            ),
            choices=[
                Choice("<25", "Under 25"),
                Choice("25_35", "25-35"),
                Choice("35_45", "35-45"),
                Choice("45_55", "45-55"),
                Choice("55+", "55+"),
                Choice("skip", "Skip this question"),
            ],
            next=next_state,
        )

    async def state_result_ineligible(self):
        return EndState(
            self,
            text="\n".join(
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
            ),
            next=self.START_STATE,
        )

    async def state_end(self):
        return EndState(
            self,
            text="\n".join(
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
            ),
            next=self.START_STATE,
        )
