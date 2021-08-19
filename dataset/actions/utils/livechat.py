import logging
import requests
from typing import Dict

from actions.utils.date import format_livechat_ts
from actions.utils.host import get_livechat_client_url
from actions.db.store import db

logger = logging.getLogger(__name__)

db.livechat.create_index("user_id")


def get_livechat(user_id=None, card_message_id=None):
    if user_id:
        return db.livechat.find_one({"user_id": user_id})
    if card_message_id:
        return db.livechat.find_one({"card_message_ids": str(card_message_id)})


def update_livechat(
    user_id,
    message: Dict = None,
    card_message_id=None,
    card_message_id_index_map: Dict = None,
    enabled=None,
):
    update_data = {}

    livechat = db.livechat.find_one({"user_id": user_id})

    set_data = {}
    push_data = {}

    if not livechat:
        set_data.update(
            {
                "user_id": user_id,
                "enabled": enabled or False,
                "card_message_ids": [],
                "card_message_id_index_map": {},
            }
        )

    if message:
        messages_to_add = [message]
        push_data.update({"messages": {"$each": messages_to_add}})

    if card_message_id:
        card_message_ids_to_add = [str(card_message_id)]
        push_data.update({"card_message_ids": {"$each": card_message_ids_to_add}})

    if card_message_id_index_map:
        db.livechat.update_one(
            {"user_id": user_id},
            [{"$set": {"card_message_id_index_map": card_message_id_index_map}}],
            upsert=True,
        )

    if enabled is not None:
        set_data.update({"enabled": enabled})

    if set_data:
        update_data.update({"$set": set_data})
    if push_data:
        update_data.update({"$push": push_data})

    if update_data:
        db.livechat.update_one(
            {"user_id": user_id},
            update_data,
            upsert=True,
        )


def get_livechat_card(user_id, message_index: int = None):
    livechat = db.livechat.find_one({"user_id": user_id})
    livechat_id = livechat.get("_id")
    messages = livechat.get("messages")
    num_messages = len(messages)
    if not (livechat and messages and num_messages):
        return

    if message_index is None:
        message_index = num_messages - 1
    if message_index < 0:
        message_index = 0
    if message_index >= num_messages:
        message_index = num_messages - 1
    display_message = messages[message_index]
    sender_type = display_message.get("sender_type")
    sent_ts = display_message.get("sent_ts")
    sent_date = format_livechat_ts(sent_ts)
    message_text = display_message.get("text")
    text = (
        f"Chat #{user_id}\n"
        + "\n"
        + f"{message_text}\n"
        + "\n"
        + f"Sent by {sender_type} on {sent_date}\n"
    )
    reply_markup = {
        "keyboard": [
            [
                {
                    "title": "<<<",
                    "payload": f'/livechat_scroll{{"d":"start"}}',
                },
                {
                    "title": "<",
                    "payload": f'/livechat_scroll{{"d":"previous"}}',
                },
                {
                    "title": ">",
                    "payload": f'/livechat_scroll{{"d":"next"}}',
                },
                {
                    "title": ">>>",
                    "payload": f'/livechat_scroll{{"d":"end"}}',
                },
            ]
        ],
        "type": "inline",
    }
    return {
        "text": text,
        "reply_markup": reply_markup,
        "is_livechat_card": True,
        "livechat_user_id": livechat.get("user_id"),
        "livechat_message_index": message_index,
    }


def post_livechat_message(user_id, message_text):
    response_json = {}
    try:
        url = get_livechat_client_url("/livechat/message")
        response = requests.post(
            url, json={"sender": user_id, "text": message_text}, timeout=5
        )
        response_json = response.json()
    except Exception as e:
        logger.error(e)

    return response_json


def scroll_livechat(card_message_id, direction):
    livechat = get_livechat(card_message_id=card_message_id)
    user_id = livechat.get("user_id")
    total_messages = len(livechat.get("messages", []))
    next_message_index = livechat.get("card_message_id_index_map", {}).get(
        str(card_message_id), 0
    )
    if direction == "start":
        next_message_index = 0
    elif direction == "previous":
        next_message_index = next_message_index - 1
    elif direction == "next":
        next_message_index = next_message_index + 1
    elif direction == "end":
        next_message_index = total_messages - 1

    if next_message_index < 0:
        next_message_index = 0
    if next_message_index >= total_messages:
        next_message_index = total_messages - 1

    card_message_id_index_map = {str(card_message_id): next_message_index}
    update_livechat(user_id, card_message_id_index_map=card_message_id_index_map)
    json_message = get_livechat_card(user_id, message_index=next_message_index)
    json_message["message_id"] = card_message_id
    return json_message
