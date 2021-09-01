from datetime import datetime
from typing import Any, Text, Dict, List
from uuid import uuid4

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from actions.utils.date import SERVER_TZINFO
from actions.utils.livechat import get_livechat_card, update_livechat


class ActionLivechatMessage(Action):
    def name(self) -> Text:
        return "action_livechat_message"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        metadata = tracker.latest_message.get("metadata")
        user_id = metadata.get("sender")
        user_message = {
            "id": uuid4(),
            "user_id": user_id,
            "text": metadata.get("text"),
            "sender_type": "user",
            "sent_ts": datetime.now(tz=SERVER_TZINFO).timestamp(),
        }
        update_livechat(user_id, message=user_message)
        json_message = get_livechat_card(user_id=user_id)
        dispatcher.utter_message(json_message=json_message)

        return []
