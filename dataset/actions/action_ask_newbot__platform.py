from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionAskNewBotName(Action):
    def name(self) -> Text:
        return "action_ask_newbot__platform"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        text = "Please choose the platform where you want to deploy the bot."
        reply_markup = {
            "keyboard": [["Web"]],
            "resize_keyboard": True,
            "row_width": 2,
        }
        dispatcher.utter_message(
            json_message={"text": text, "reply_markup": reply_markup}
        )
        return []
