from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from actions.utils.admin_config import get_admin_group_id
from actions.utils.entity import get_entity
from actions.utils.json import get_json_key
from actions.utils.livechat import (
    get_livechat,
    get_livechat_card,
    update_livechat,
)
from actions.utils.message_metadata import get_message_metadata


class ActionLivechatTag(Action):
    def name(self) -> Text:
        return "action_livechat_tag"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        entities = tracker.latest_message.get("entities", [])
        lifecycle_stage = get_entity(entities, "d")

        metadata = tracker.latest_message.get("metadata")
        callback_query_message = get_json_key(metadata, "callback_query.message")
        callback_query_message_id = callback_query_message.get("message_id")
        message_metadata = get_message_metadata(callback_query_message_id) or {}
        livechat = get_livechat(id=message_metadata.get("livechat_id"))
        user_id = livechat.get("user_id")

        user_metadata = {
            "lifecycle_stage": lifecycle_stage,
        }

        update_livechat(user_id, user_metadata=user_metadata)

        json_message = get_livechat_card(
            user_id=user_id, message_id=callback_query_message_id
        )
        json_message["message_id"] = callback_query_message_id
        json_message["chat_id"] = get_admin_group_id()
        json_message["remove_reply_markup"] = False
        dispatcher.utter_message(json_message=json_message)

        return []
