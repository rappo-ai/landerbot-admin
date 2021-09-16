from math import ceil
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


def paginate_inline_button(
    inline_buttons,
    selector,
    page_index=0,
    row_width=4,
    max_rows=10,
):
    paginated_buttons = []
    total_buttons = len(inline_buttons)
    total_rows = ceil(total_buttons / row_width)
    total_pages = ceil(total_rows / max_rows)

    clamp = lambda val, min, max: min if val < min else max if val > max else val

    page_index = clamp(page_index, 0, total_pages - 1)
    num_rows = clamp(total_rows - (page_index * max_rows), 0, max_rows)
    slice_start = page_index * max_rows * row_width

    for i in range(num_rows):
        slice_end = slice_start + row_width
        sliced_list = inline_buttons[slice_start:slice_end]
        if sliced_list:
            paginated_buttons.append(sliced_list)
        slice_start += row_width

    if total_pages > 1:
        scroll_buttons = []
        if page_index > 0:
            scroll_buttons.append(
                {
                    "title": "«",
                    "payload": f'/chats{{"s":"{selector}","i":{page_index-1}}}',
                }
            )
        if page_index < (total_pages - 1):
            scroll_buttons.append(
                {
                    "title": "»",
                    "payload": f'/chats{{"s":"{selector}","i":{page_index+1}}}',
                }
            )
        paginated_buttons.append(scroll_buttons)

    return paginated_buttons


def get_chat_inline_button(chat, selector):
    return {
        "title": f"{get_json_key(chat, 'user_metadata.user_name', chat.get('user_id'))}",
        "payload": f'/chats{{"p":"{selector}","u":"{chat.get("user_id")}"}}',
    }


def format_chats_message(chats, selector, page_index):
    ROW_WIDTH = 4
    MAX_ROWS = 10
    chats_keyboard = paginate_inline_button(
        [get_chat_inline_button(c, selector) for c in chats],
        selector,
        page_index,
        ROW_WIDTH,
        MAX_ROWS,
    )

    reply_markup = {
        "keyboard": [
            *chats_keyboard,
            [
                {
                    "title": "🔄 Refresh",
                    "payload": f'/chats{{"s":"{selector}"}}',
                },
                {
                    "title": "↩️ Back",
                    "payload": f"/chats",
                },
            ],
        ],
        "type": "inline",
        "row_width": ROW_WIDTH,
    }
    return {
        "text": f"{str(selector).capitalize()} chats: {'' if chats_keyboard else 'No chats found'}",
        "reply_markup": reply_markup,
    }


def get_all_chats_message(page_index):
    all_chats = get_livechats()
    return format_chats_message(all_chats, "all", page_index)


def get_online_chats_message(page_index):
    online_chats = get_livechats(online=True)
    return format_chats_message(online_chats, "online", page_index)


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
        page_index = get_entity(entities, "i", 0)

        metadata = tracker.latest_message.get("metadata", {})
        callback_query_message = get_json_key(metadata, "callback_query.message", {})
        callback_query_message_id = callback_query_message.get("message_id")

        json_message = {}
        if selector == "all":
            json_message = get_all_chats_message(page_index)
        elif selector == "online":
            json_message = get_online_chats_message(page_index)
        elif not selector:
            if user_id and callback_query_message_id:
                back_button_title = (
                    f"↩️ Back to {str(parent_selector).capitalize()} chats"
                )
                back_button_payload = (
                    f'/chats{{"s":"{parent_selector}", "i":{page_index}}}'
                )
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
