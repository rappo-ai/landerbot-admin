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
        user_id = metadata.get("sender_id")
        sender_type = metadata.get("sender_type", "user")
        message_text = metadata.get("message_text")
        if message_text:
            user_message = {
                "id": uuid4(),
                "user_id": user_id,
                "text": message_text,
                "sender_type": sender_type,
                "sent_ts": datetime.now(tz=SERVER_TZINFO).timestamp(),
            }
            update_livechat(user_id, message=user_message)
        user_metadata = metadata.get("user_metadata")
        if user_metadata:
            update_livechat(user_id, user_metadata=user_metadata)

        send_notification = metadata.get("send_notification")
        if send_notification:
            notification_type = metadata.get("notification_type", "transcript")
            json_message = get_livechat_card(
                user_id=user_id, notification_type=notification_type
            )
            json_message["remove_reply_markup"] = False
            dispatcher.utter_message(json_message=json_message)

        return []
