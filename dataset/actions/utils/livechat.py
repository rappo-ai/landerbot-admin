from bson.objectid import ObjectId
from datetime import datetime
import logging
from pymongo import DESCENDING
import requests
from typing import Dict

from actions.db.store import db

from actions.utils.date import SERVER_TZINFO
from actions.utils.host import get_livechat_client_url
from actions.utils.message_metadata import get_message_metadata
from actions.utils.name import random_animal_name

logger = logging.getLogger(__name__)

db.livechat.create_index("user_id")
db.livechat.create_index("sessions.start_ts")


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
    lifecycle_stage=None,
    from_ts=None,
    to_ts=None,
):
    query = {}
    if enabled:
        query.update({"enabled": enabled})
    if online:
        query.update({"online": online})
    if visible:
        query.update({"visible": visible})
    if lifecycle_stage:
        query.update({"user_metadata.lifecycle_stage": lifecycle_stage})

    ts_query = {}
    if from_ts:
        ts_query.update({"$gte": from_ts})
    if to_ts:
        ts_query.update({"$lt": to_ts})
    if ts_query:
        query.update({"sessions": {"$elemMatch": {"start_ts": ts_query}}})

    return db.livechat.find(query).sort("_id", DESCENDING)


def get_livechat_stats(
    lifecycle_stage=None,
    from_ts=None,
    to_ts=None,
):
    pipeline = []

    # filter documents that do not match the lifecycle_stage
    if lifecycle_stage:
        pipeline.append({"$match": {"user_metadata.lifecycle_stage": lifecycle_stage}})

    # remove sessions that don't fit the date criteria; also remove active sessions (duration is not set)
    sessions_cond_query = []
    sessions_cond_query.append({"$gt": ["$$session.duration_ts", 0]})
    if from_ts:
        sessions_cond_query.append({"$gte": ["$$session.start_ts", from_ts]})
    if to_ts:
        sessions_cond_query.append({"$lt": ["$$session.start_ts", to_ts]})
    sessions_project_query = {
        "$filter": {
            "input": "$sessions",
            "as": "session",
            "cond": {"$and": sessions_cond_query},
        }
    }
    pipeline.append(
        {
            "$project": {
                "user_id": 1,
                "events": 1,
                "user_metadata": 1,
                "sessions": sessions_project_query,
            }
        }
    )
    # filter documents with at least one session that matches the session criteria (see above)
    pipeline.append({"$match": {"$expr": {"$gt": [{"$size": "$sessions"}, 0]}}})

    # compute the valid session indexes for each document (used next to filter events)
    pipeline.append(
        {
            "$group": {
                "_id": "$_id",
                "user_id": {"$first": "$user_id"},
                "events": {"$first": "$events"},
                "user_metadata": {"$first": "$user_metadata"},
                "sessions": {"$first": "$sessions"},
                "valid_session_indexes": {"$first": "$sessions.index"},
            }
        }
    )

    # remove events that are not in a valid session; also remove other unnecessary events to make computations easier downstream
    pipeline.append(
        {
            "$project": {
                "user_id": 1,
                "events": {
                    "$filter": {
                        "input": "$events",
                        "as": "event",
                        "cond": {
                            "$and": [
                                {
                                    "$in": [
                                        "$$event.session_index",
                                        "$valid_session_indexes",
                                    ]
                                },
                                {
                                    "$or": [
                                        {"$ne": ["$$event.label", "/livechat_visible"]},
                                        {"$eq": ["$$event.metadata.visible", True]},
                                    ]
                                },
                                {
                                    "$or": [
                                        {"$ne": ["$$event.label", "enable_livechat"]},
                                        {"$eq": ["$$event.value", True]},
                                    ]
                                },
                            ],
                        },
                    }
                },
                "user_metadata": 1,
                "sessions": 1,
            }
        }
    )

    # compute aggregate stats
    pipeline.append(
        {
            "$group": {
                "_id": None,
                "total_users": {"$sum": 1},
                "new_users": {
                    "$sum": {
                        "$cond": [
                            {"$in": [0, "$sessions.index"]},
                            1,
                            0,
                        ]
                    }
                },
                "returning_users": {
                    "$sum": {
                        "$cond": [
                            {"$in": [0, "$sessions.index"]},
                            0,
                            1,
                        ]
                    }
                },
                "widget_open": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["/livechat_visible", "$events.label"]},
                            1,
                            0,
                        ]
                    }
                },
                "pricing": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["/pricing", "$events.label"]},
                            1,
                            0,
                        ]
                    }
                },
                "features": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["/features", "$events.label"]},
                            1,
                            0,
                        ]
                    }
                },
                "installation": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["/installation", "$events.label"]},
                            1,
                            0,
                        ]
                    }
                },
                "about": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["/about", "$events.label"]},
                            1,
                            0,
                        ]
                    }
                },
                "contact": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["/contact", "$events.label"]},
                            1,
                            0,
                        ]
                    }
                },
                "live_chat_enabled": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["enable_livechat", "$events.label"]},
                            1,
                            0,
                        ]
                    }
                },
                "subscribe": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["/subscribe", "$events.label"]},
                            1,
                            0,
                        ]
                    }
                },
                "qualified_lead": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$user_metadata.lifecycle_stage", "lead"]},
                            1,
                            0,
                        ]
                    }
                },
                "unqualified": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$user_metadata.lifecycle_stage", "unqualified"]},
                            1,
                            0,
                        ]
                    }
                },
                "untagged": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$user_metadata.lifecycle_stage", "subscriber"]},
                            1,
                            0,
                        ]
                    }
                },
                "total_session_duration": {
                    "$sum": {
                        "$reduce": {
                            "input": "$sessions.duration_ts",
                            "initialValue": 0,
                            "in": {"$sum": ["$$value", "$$this"]},
                        }
                    }
                },
                "total_sessions": {"$sum": {"$size": "$sessions"}},
                "sessions_per_user": {"$avg": {"$size": "$sessions"}},
                "cities": {"$push": "$user_metadata.location_data.city"},
                "countries": {"$push": "$user_metadata.location_data.country"},
                "form_factors": {"$push": "$user_metadata.wurfl_data.form_factor"},
                "devices": {"$push": "$user_metadata.wurfl_data.complete_device_name"},
                "browsers": {"$push": "$user_metadata.browser_data.browserName"},
                "referrers": {"$push": "$user_metadata.referrer_data.referrer"},
            }
        }
    )

    livechat_stats = {}
    aggregation_result = db.livechat.aggregate(pipeline)
    for r in aggregation_result:
        livechat_stats = r

    total_session_duration = livechat_stats.get("total_session_duration", 0)
    total_sessions = livechat_stats.get("total_sessions", 0)
    if total_sessions:
        livechat_stats["session_duration"] = total_session_duration / total_sessions
    else:
        livechat_stats["session_duration"] = 0

    funnel_keys = [
        "total_users",
        "new_users",
        "returning_users",
        "widget_open",
        "pricing",
        "features",
        "installation",
        "about",
        "contact",
        "live_chat_enabled",
        "subscribe",
        "qualified_lead",
        "unqualified",
        "untagged",
    ]
    livechat_stats["funnel"] = {}
    for k in funnel_keys:
        val = livechat_stats.pop(k, 0)
        livechat_stats["funnel"][k] = val

    livechat_stats["averages"] = {}
    averages_keys = ["sessions_per_user", "session_duration"]
    for k in averages_keys:
        val = livechat_stats.pop(k, 0)
        livechat_stats["averages"][k] = val

    lists_keys = [
        "cities",
        "countries",
        "form_factors",
        "devices",
        "browsers",
        "referrers",
    ]
    livechat_stats["lists"] = {}
    for k in lists_keys:
        val = livechat_stats.pop(k, [])
        livechat_stats["lists"][k] = val

    return livechat_stats


def update_livechat(
    user_id,
    user_metadata: Dict = None,
    message: Dict = None,
    event: Dict = None,
    enabled=None,
    online=None,
    visible=None,
):
    update_data = {}

    livechat = db.livechat.find_one({"user_id": user_id})

    if not livechat:
        livechat_id = db.livechat.insert_one(
            {
                "creation_ts": datetime.now(tz=SERVER_TZINFO).timestamp(),
                "last_update_ts": datetime.now(tz=SERVER_TZINFO).timestamp(),
                "user_id": user_id,
                "user_metadata": {
                    "user_name": random_animal_name(),
                    "lifecycle_stage": "subscriber",
                },
                "enabled": False,
                "online": False,
                "visible": False,
                "sessions": [],
                "messages": [],
                "events": [],
            },
        ).inserted_id
        livechat = db.livechat.find_one({"_id": livechat_id})

    sessions = livechat.get("sessions", [])
    session_index = max(len(sessions) - 1, 0)
    session = sessions[session_index] if sessions else {}
    if event:
        event.update({"session_index": session_index})
    events = [event] if event else []

    set_data = {}
    push_data = {}

    if message:
        messages_to_add = [message]
        push_data.update({"messages": {"$each": messages_to_add}})

    if enabled is not None:
        set_data.update({"enabled": enabled})
        events.append(
            {
                "category": "user",
                "action": "update_livechat",
                "label": "enable_livechat",
                "value": enabled,
                "session_index": session_index,
                "ts": datetime.now(tz=SERVER_TZINFO).timestamp(),
            }
        )

    if online is not None:
        set_data.update({"online": online})
        if online:
            sessions_to_add = [
                {
                    "start_ts": datetime.now(tz=SERVER_TZINFO).timestamp(),
                    "index": len(sessions),
                }
            ]
            push_data.update({"sessions": {"$each": sessions_to_add}})
        else:
            end_ts = datetime.now(tz=SERVER_TZINFO).timestamp()
            duration_ts = end_ts - session.get("start_ts", end_ts)
            set_data.update(
                {
                    f"sessions.{session_index}.end_ts": end_ts,
                    f"sessions.{session_index}.duration_ts": duration_ts,
                }
            )

    if events:
        push_data.update({"events": {"$each": events}})

    if visible is not None:
        set_data.update({"visible": visible})

    if user_metadata:
        merged_user_metadata = livechat.get("user_metadata", {})
        merged_user_metadata.update(user_metadata)
        set_data.update({"user_metadata": merged_user_metadata})

    if set_data or push_data:
        set_data.update({"last_update_ts": datetime.now(tz=SERVER_TZINFO).timestamp()})
    if set_data:
        update_data.update({"$set": set_data})
    if push_data:
        update_data.update({"$push": push_data})

    if update_data:
        db.livechat.update_one(
            {"user_id": user_id},
            update_data,
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
        for message in messages:
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

        wurfl_data = user_metadata.get("wurfl_data", {})
        device = wurfl_data.get("form_factor", "?")
        if device != "?":
            device = device + f" ({wurfl_data.get('complete_device_name', '?')})"

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
                "🆕 New Visitor" if lifecycle_stage == "subscriber" else "❌ Unqualified"
            )
        )

        card_text = (
            card_text
            + "\n"
            + f"Status: {chat_status}\nLocation: {location}\nLead Status: {lead_status}\nDevice: {device}\nBrowser: {browser}\nReferrer: {referrer}\nSessions: {num_sessions}\n"
        )

        reply_markup = {
            "keyboard": [
                [
                    {
                        "title": "🔄 Refresh",
                        "payload": f"/refresh",
                    },
                ],
                [
                    {
                        "title": "🙋 Greet",
                        "payload": f'/quick{{"d":"greet"}}',
                    },
                    {
                        "title": "👋 Close",
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
                        "title": "🔍 Expand",
                        "payload": f"/refresh",
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
