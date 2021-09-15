from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from actions.utils.admin_config import get_admin_group_id
from actions.utils.entity import get_entity
from actions.utils.json import get_json_key
from actions.utils.livechat import (
    get_livechats,
    get_livechat_card,
)
from actions.utils.message_metadata import update_message_metadata


def get_menu_message():
    return {
        "text": "Select which chats you want to see:",
        "reply_markup": {
            "keyboard": [
                [
                    {
                        "title": "🟢 Online",
                        "payload": f'/chats{{"s":"online"}}',
                    },
                    {
                        "title": "🔷 All",
                        "payload": f'/chats{{"s":"all"}}',
                    },
                ],
            ],
            "type": "inline",
        },
    }


def format_chats_message(chats, selector):
    chats_keyboard = [
        {
            "title": f"{get_json_key(c, 'user_metadata.user_name', c.get('user_id'))}",
            "payload": f'/chats{{"p":"{selector}","u":"{c.get("user_id")}"}}',
        }
        for c in chats
    ]
    reply_markup = {
        "keyboard": [
            chats_keyboard,
            [
                {
                    "title": "Refresh",
                    "payload": f'/chats{{"s":"{selector}"}}',
                },
            ],
        ],
        "type": "inline",
    }
    return {
        "text": f"{str(selector).capitalize()} chats: {'' if chats_keyboard else 'No chats found'}",
        "reply_markup": reply_markup,
    }


def get_all_chats_message():
    all_chats = get_livechats()
    return format_chats_message(all_chats, "all")


def get_online_chats_message():
    online_chats = get_livechats(online=True)
    return format_chats_message(online_chats, "online")


class ActionListChats(Action):
    def name(self) -> Text:
        return "action_list_chats"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        entities = tracker.latest_message.get("entities", [])
        selector = get_entity(entities, "s")
        parent_selector = get_entity(entities, "p")
        user_id = get_entity(entities, "u")

        metadata = tracker.latest_message.get("metadata", {})
        callback_query_message = get_json_key(metadata, "callback_query.message", {})
        callback_query_message_id = callback_query_message.get("message_id")

        json_message = {}
        if selector == "all":
            json_message = get_all_chats_message()
        elif selector == "online":
            json_message = get_online_chats_message()
        elif not selector:
            if user_id and callback_query_message_id:
                back_button_title = (
                    f"↩️ Back to {str(parent_selector).capitalize()} chats"
                )
                back_button_payload = f'/chats{{"s":"{parent_selector}"}}'
                update_message_metadata(
                    message_id=callback_query_message_id,
                    metadata={
                        "back_button_title": back_button_title,
                        "back_button_payload": back_button_payload,
                    },
                )

                json_message = get_livechat_card(
                    user_id=user_id, message_id=callback_query_message_id
                )
            else:
                json_message = get_menu_message()

        if json_message:
            if callback_query_message_id:
                json_message["message_id"] = callback_query_message_id
                json_message["chat_id"] = get_admin_group_id()
            dispatcher.utter_message(json_message=json_message)

        return []
