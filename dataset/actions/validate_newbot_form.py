from typing import Any, Dict, List, Text

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict


class ValidateNewBotForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_newbot_form"

    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> List[Text]:

        return slots_mapped_in_domain

    def validate_newbot__name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        bot_name: Text = slot_value
        if bot_name.count("\n") or bot_name.count("\t"):
            dispatcher.utter_message(
                json_message={"text": "Name should not contain any newlines or tabs."}
            )
            return {"newbot__name": None}

        else:
            return {"newbot__name": bot_name}
