import logging
import requests
from typing import Dict

from actions.utils.host import get_livechat_client_url
from actions.db.store import db

logger = logging.getLogger(__name__)

db.livechat.create_index("user_id")


def get_livechat(user_id=None, card_message_id=None):
    if user_id:
        return db.livechat.find_one({"user_id": user_id})
    if card_message_id:
        return db.livechat.find_one({"card_message_ids": str(card_message_id)})


def update_livechat(user_id, message: Dict = None, card_message_id=None):
    update = {}

    livechat = db.livechat.find_one({"user_id": user_id})
    if not livechat:
        livechat = {"user_id": user_id, "enabled": True}  # tbd
        update.update({"$set": livechat})

    if message:
        messages = [message]
        update.update({"$push": {"messages": {"$each": messages}}})

    if card_message_id:
        update.update({"$push": {"card_message_ids": str(card_message_id)}})

    db.livechat.update_one(
        {"user_id": user_id},
        update,
        upsert=True,
    )


def get_livechat_card(user_id, message_id=None):
    livechat = db.livechat.find_one({"user_id": user_id})
    messages = livechat.get("messages")
    num_messages = len(messages)
    if not (livechat and messages and num_messages):
        return

    display_message = None
    if message_id:
        display_message = next((x for x in messages if x.get("id") == message_id), {})
    else:
        display_message = messages[num_messages - 1]
    sender_type = display_message.get("sender_type")
    sent_date = display_message.get("sent_date")
    message_text = display_message.get("text")
    text = f"{message_text}\n" + "\n" + f"Sent by {sender_type} on {sent_date}\n"
    return {
        "text": text,
        "is_livechat_card": True,
        "livechat_user_id": livechat.get("user_id"),
    }


def post_livechat_message(user_id, message_text):
    response_json = {}
    try:
        url = get_livechat_client_url("/livechat/message")
        response = requests.post(
            url, json={"sender": user_id, "text": message_text}, timeout=1
        )
        response_json = response.json()
    except Exception as e:
        logger.error(e)

    return response_json
