from typing import List

from who.base_application import BaseApplication
from who.models import Message
from who.states import Choice, ChoiceState, EndState, ErrorMessage, FreeText


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
            return "state_gender"

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
                    "",
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

    async def state_gender(self):
        return ChoiceState(
            self,
            question="\n".join(["⬛⬛⬜⬜⬜", "", "What gender do you identify as?", ""]),
            error="\n".join(
                [
                    "⚠️ This service works best when you use the numbered options "
                    "available",
                    "",
                    "Please confirm your gender or skip.",
                ]
            ),
            choices=[
                Choice("male", "Male"),
                Choice("female", "Female"),
                Choice("other", "Other"),
                Choice("not_say", "Rather not say"),
                Choice("skip", "Skip this question"),
            ],
            next="state_smoking_frequency",
        )

    async def state_smoking_frequency(self):
        return ChoiceState(
            self,
            question="\n".join(["⬛⬛⬛⬜⬜", "", "How often do you use tobacco?", ""]),
            error="\n".join(
                [
                    "⚠️ This service works best when you use the numbered options "
                    "available",
                    "",
                    "Please confirm your gender or skip.",
                ]
            ),
            choices=[
                Choice("daily", "Daily"),
                Choice("weekly", "Weekly"),
                Choice("now_and_then", "Every now and then"),
                Choice("socially", "Only socially"),
                Choice("skip", "Skip this question"),
            ],
            next="state_tobacco_type",
        )

    async def state_tobacco_type(self):
        return ChoiceState(
            self,
            question="\n".join(
                ["⬛⬛⬛⬛⬜", "", "What type of tobacco products do you usually use?", ""]
            ),
            error="\n".join(
                [
                    "⚠️ This service works best when you use the numbered options "
                    "available",
                    "",
                    "Please confirm your tobacco type or skip.",
                ]
            ),
            choices=[
                Choice(
                    "smoked",
                    "Smoked tobacco - _includes cigarettes, cigars, cigarillos, "
                    "roll-your-own, shisha (also known as hookah or waterpipe), "
                    "kreteks and bidis_",
                ),
                Choice(
                    "smokeless",
                    "Smokeless tobacco - _includes chewing tobacco, snuff, and snus_",
                ),
                Choice("heatead", "Heated tobacco products "),
                Choice("multiple", "More than one type of tobacco product"),
                Choice("other", "Other"),
                Choice("skip", "Skip this question"),
            ],
            next="state_smoking_spend",
        )

    async def state_smoking_spend(self):
        async def validate_amount(value):
            try:
                assert isinstance(value, str)
                assert value.isdigit()
            except AssertionError:
                raise ErrorMessage("⚠️ Please enter a valid amount")

        return FreeText(
            self,
            question="\n".join(
                [
                    "⬛⬛⬛⬛⬛⬛⬜",
                    "",
                    "How much do you spend on tobacco products weekly?",
                    "_Only send the amount in numbers_",
                    "",
                    "Type *SKIP* to move on to the next step in the Quit Challenge.",
                ]
            ),
            next="state_quit_reason",
            check=validate_amount,
        )

    async def state_quit_reason(self):
        # TODO: Add additional capture for "Other"
        return ChoiceState(
            self,
            question="\n".join(
                [
                    "⬛⬛⬛⬛⬛",
                    "",
                    "Can you share one reason you're motivated to quit tobacco?",
                    "",
                    "_Select a number from the list below, or reply with *7* "
                    "to type out your own reason_",
                    "",
                ]
            ),
            error="\n".join(
                [
                    "⚠️ This service works best when you use the numbered options "
                    "available",
                    "",
                    "Please select a number from the list below, or reply with *7* "
                    "to type out your own reason.",
                ]
            ),
            choices=[
                Choice(
                    "covid_19",
                    "🦠 to protect yourself from getting a severe case of COVID-19",
                ),
                Choice(
                    "good_example",
                    "👍 to set a good example for your family and friends",
                ),
                Choice("save_money", "💸 to save money"),
                Choice("environment", "🌳 to protect the environment"),
                Choice("health", "🫁 to maintain a healthier body and lifestyle"),
                Choice("health_others", "👶 to reduce health risks of those around you"),
                Choice("other", "Other "),
                Choice("skip", "Skip"),
            ],
            next="state_quit_next",
        )

    async def state_quit_next(self):
        return ChoiceState(
            self,
            question="\n".join(
                [
                    "*That's great! Try to keep this motivation in mind "
                    "throughout your quit journey.* 💪",
                    "",
                    "Type *NEXT* to move on to the next step in the Quit Challenge.",
                    ""
                ]
            ),
            error="\n".join(
                [
                    "⚠️ This service works best when you use the numbered options "
                    "available",
                    "",
                    "Please type 1 or NEXT.",
                ]
            ),
            choices=[Choice("next", "Next")],
            next="state_end",
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
