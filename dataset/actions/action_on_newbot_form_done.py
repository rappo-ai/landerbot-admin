from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from actions.utils.bot import add_bot, get_bot_json_message


class ActionOnNewBotFormDone(Action):
    def name(self) -> Text:
        return "action_on_newbot_form_done"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        bot_name = tracker.get_slot("newbot__name")
        bot_platform = tracker.get_slot("newbot__platform")
        bot_id = add_bot(bot_name, bot_platform)

        dispatcher.utter_message(
            text="Done! Congratulations on your new Rappo bot. You can now start designing your bot. Start by choosing from our library of bot templates, then customise everything - messages, buttons, transitions, UI and more. Once you are done click Publish for steps to make your bot live."
        )

        json_message = get_bot_json_message(view="bot", bot_id=bot_id, show_bots_list_button=False)
        )
        dispatcher.utter_message(json_message=json_message)

        return []
