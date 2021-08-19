from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from actions.utils.entity import get_entity
from actions.utils.json import get_json_key
from actions.utils.livechat import scroll_livechat


class ActionLivechatScroll(Action):
    def name(self) -> Text:
        return "action_livechat_scroll"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        entities = tracker.latest_message.get("entities", [])
        direction = get_entity(entities, "d", "start")
        metadata = tracker.latest_message.get("metadata")
        message_id = get_json_key(metadata, "callback_query.message.message_id")
        json_message = scroll_livechat(card_message_id=message_id, direction=direction)
        json_message["chat_id"] = tracker.sender_id
        dispatcher.utter_message(json_message=json_message)

        return []
