from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionMainMenu(Action):
    def name(self) -> Text:
        return "action_main_menu"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        text = "I can help you create and manage Rappo Live Chat bots.\n\nYou can control me by sending these commands:\n\n/newbot - create a new bot\n/mybots - edit your bots"
        json_message = {"text": text}

        dispatcher.utter_message(json_message=json_message)

        return []
