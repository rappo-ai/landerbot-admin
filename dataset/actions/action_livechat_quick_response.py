from datetime import datetime
from typing import Any, Text, Dict, List
from uuid import uuid4

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from actions.utils.admin_config import get_admin_group_id
from actions.utils.date import SERVER_TZINFO
from actions.utils.entity import get_entity
from actions.utils.json import get_json_key
from actions.utils.livechat import (
    get_livechat,
    get_livechat_card,
    post_livechat_message,
    update_livechat,
)
from actions.utils.message_metadata import get_message_metadata


class ActionLivechatQuickResponse(Action):
    def name(self) -> Text:
        return "action_livechat_quick_response"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        entities = tracker.latest_message.get("entities", [])
        selector = get_entity(entities, "d")
        first_name = tracker.get_slot("first_name")

        metadata = tracker.latest_message.get("metadata")
        callback_query_message = get_json_key(metadata, "callback_query.message")
        callback_query_message_id = callback_query_message.get("message_id")

        message_metadata = get_message_metadata(callback_query_message_id) or {}
        livechat = get_livechat(id=message_metadata.get("livechat_id"))
        user_id = livechat.get("user_id")

        quick_responses_map = {
            "greet": f"Hi, you are chatting with {first_name} from Rappo.",
            "close": f"Thank you for chatting with us. I hope we were able to help you out. If you have any other queries, do ping us and we'll get back to you right away.",
        }
        message_text = quick_responses_map.get(selector or "")
        enable_livechat = False if selector == "close" else True

        bot_message = {
            "id": uuid4(),
            "bot_id": tracker.sender_id,  # tbd - bot collection
            "text": message_text,
            "sender_type": "admin",
            "sent_ts": datetime.now(tz=SERVER_TZINFO).timestamp(),
        }
        update_livechat(user_id, message=bot_message, enabled=enable_livechat)

        post_livechat_message(user_id, message_text=message_text)

        json_message = get_livechat_card(
            user_id=user_id, message_id=callback_query_message_id
        )
        json_message["message_id"] = callback_query_message_id
        json_message["chat_id"] = get_admin_group_id()
        json_message["remove_reply_markup"] = False
        dispatcher.utter_message(json_message=json_message)

        return []
