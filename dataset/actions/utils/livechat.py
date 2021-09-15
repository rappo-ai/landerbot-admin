from bson.objectid import ObjectId
from datetime import datetime
import logging
import requests
from typing import Dict

from actions.db.store import db

from actions.utils.date import SERVER_TZINFO
from actions.utils.host import get_livechat_client_url
from actions.utils.message_metadata import get_message_metadata
from actions.utils.name import random_animal_name

logger = logging.getLogger(__name__)

db.livechat.create_index("user_id")


def get_livechat(
    id=None,
    user_id=None,
):
    query = {}
    if id:
        query.update({"_id": ObjectId(id)})
    if user_id:
        query.update({"user_id": user_id})
    return db.livechat.find_one(query)


def get_livechats(
    enabled=None,
    online=None,
    visible=None,
):
    query = {}
    if enabled:
        query.update({"enabled": enabled})
    if online:
        query.update({"online": online})
    if visible:
        query.update({"visible": visible})
    return db.livechat.find(query)


def update_livechat(
    user_id,
    user_metadata: Dict = None,
    message: Dict = None,
    enabled=None,
    online=None,
    visible=None,
):
    update_data = {}

    livechat = db.livechat.find_one({"user_id": user_id})

    if not livechat:
        livechat_id = db.livechat.insert_one(
            {
                "user_id": user_id,
                "user_metadata": {
                    "user_name": random_animal_name(),
                    "lifecycle_stage": "subscriber",
                },
                "enabled": False,
                "online": False,
                "visible": False,
                "sessions": [],
            },
        ).inserted_id
        livechat = db.livechat.find_one({"_id": livechat_id})

    set_data = {}
    push_data = {}

    if message:
        messages_to_add = [message]
        push_data.update({"messages": {"$each": messages_to_add}})

    if enabled is not None:
        set_data.update({"enabled": enabled})

    if online is not None:
        set_data.update({"online": online})
        if online:
            sessions_to_add = [{"start_ts": datetime.now(tz=SERVER_TZINFO).timestamp()}]
            push_data.update({"sessions": {"$each": sessions_to_add, "$position": 0}})
        else:
            set_data.update(
                {"sessions.0.end_ts": datetime.now(tz=SERVER_TZINFO).timestamp()}
            )

    if visible is not None:
        set_data.update({"visible": visible})

    if user_metadata:
        merged_user_metadata = livechat.get("user_metadata", {})
        merged_user_metadata.update(user_metadata)
        set_data.update({"user_metadata": merged_user_metadata})

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


def get_livechat_card(user_id, notification_type="transcript", message_id=None):
    livechat = db.livechat.find_one({"user_id": user_id})
    user_metadata = livechat.get("user_metadata", {})
    messages = livechat.get("messages") or []

    user_name = user_metadata.get("user_name", "") + f" #{str(user_id)[-7:]}"
    card_text = ""

    reply_markup = {}

    if notification_type == "transcript":
        card_text = card_text + f"Chat with {user_name}\n\n"
        for message in reversed(messages):
            sender_type = str(message.get("sender_type")).capitalize()
            card_text = card_text + f"{sender_type}: {message.get('text')}\n"

        chat_status = "🟢 Online" if livechat.get("online", False) else "🔴 Offline"
        if livechat.get("online") == True and livechat.get("visible") == True:
            chat_status = chat_status + " + 📖 Open"
        if livechat.get("online") == True and livechat.get("enabled") == True:
            chat_status = chat_status + " + ❤️ Live"

        browser_data = user_metadata.get("browser_data", {})
        browser = (
            browser_data.get("browserName", "?")
            + " "
            + browser_data.get("fullVersion", "?")
        )
        device = browser_data.get("userAgent", "?")

        location_data = user_metadata.get("location_data", {})
        location = (
            location_data.get("city", "?") + ", " + location_data.get("country", "?")
        )

        referrer_data = user_metadata.get("referrer_data", {})
        referrer = referrer_data.get("referrer", "?")

        sessions = livechat.get("sessions", [])
        num_sessions = len(sessions)

        lifecycle_stage = user_metadata.get("lifecycle_stage", "subscriber")
        lead_status = (
            "✅ Qualified Lead"
            if lifecycle_stage == "lead"
            else (
                "❓ New Visitor" if lifecycle_stage == "subscriber" else "❌ Unqualified"
            )
        )

        card_text = (
            card_text
            + "\n"
            + f"Status: {chat_status}\nLocation: {location}\nBrowser: {browser}\nReferrer: {referrer}\nSessions: {num_sessions}\nLead Status: {lead_status}\nDevice: {device}\n"
        )

        reply_markup = {
            "keyboard": [
                [
                    {
                        "title": "Refresh",
                        "payload": f"/refresh",
                    },
                ],
                [
                    {
                        "title": "↩️ Greet",
                        "payload": f'/quick{{"d":"greet"}}',
                    },
                    {
                        "title": "↩️ Close",
                        "payload": f'/quick{{"d":"close"}}',
                    },
                ],
                [
                    {
                        "title": "✅ Qualified Lead",
                        "payload": f'/tag{{"d":"lead"}}',
                    },
                    {
                        "title": "❌ Unqualified",
                        "payload": f'/tag{{"d":"unqualified"}}',
                    },
                ],
            ],
            "type": "inline",
        }
    elif notification_type == "latest_user_message":
        for message in reversed(messages):
            if message.get("sender_type") == "user":
                card_text = f"{message.get('text')}\n\nSent by {user_name}"
                break

        reply_markup = {
            "keyboard": [
                [
                    {
                        "title": "Expand",
                        "payload": f"/livechat_refresh",
                    },
                ]
            ],
            "type": "inline",
        }

    if message_id:
        message_metadata = get_message_metadata(message_id) or {}
        back_button_title = message_metadata.get("back_button_title")
        back_button_payload = message_metadata.get("back_button_payload")
        if back_button_title and back_button_payload:
            reply_markup["keyboard"].append(
                [{"title": back_button_title, "payload": back_button_payload}]
            )

    return {
        "text": card_text,
        "reply_markup": reply_markup,
        "message_metadata": {
            "livechat_id": str(livechat.get("_id")),
        },
    }


def post_livechat_message(user_id, message_text):
    response_json = {}
    try:
        url = get_livechat_client_url("/livechat/message")
        response = requests.post(
            url, json={"sender_id": user_id, "text": message_text}, timeout=5
        )
        response_json = response.json()
    except Exception as e:
        logger.error(e)

    return response_json
