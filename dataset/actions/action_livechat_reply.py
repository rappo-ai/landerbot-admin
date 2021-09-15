from datetime import datetime
from typing import Any, Text, Dict, List
from uuid import uuid4

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from actions.utils.date import SERVER_TZINFO
from actions.utils.json import get_json_key
from actions.utils.livechat import (
    get_livechat,
    post_livechat_message,
    update_livechat,
)
from actions.utils.message_metadata import get_message_metadata


class ActionLivechatReply(Action):
    def name(self) -> Text:
        return "action_livechat_reply"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        metadata = tracker.latest_message.get("metadata")
        message_text = get_json_key(metadata, "message.text")
        reply_to_message = get_json_key(metadata, "message.reply_to_message")
        reply_to_message_id = reply_to_message.get("message_id")
        message_metadata = get_message_metadata(reply_to_message_id) or {}
        livechat = get_livechat(id=message_metadata.get("livechat_id"))
        user_id = livechat.get("user_id")

        bot_message = {
            "id": uuid4(),
            "bot_id": tracker.sender_id,  # tbd - bot collection
            "text": message_text,
            "sender_type": "admin",
            "sent_ts": datetime.now(tz=SERVER_TZINFO).timestamp(),
        }
        update_livechat(user_id, message=bot_message, enabled=True)

        post_livechat_message(user_id, message_text=message_text)

        return []
