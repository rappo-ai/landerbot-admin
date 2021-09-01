from bson.objectid import ObjectId
from typing import Dict, Text
from secrets import token_hex

from actions.db.store import db
from actions.utils.json import get_json_key


def add_bot(bot_name: Text, bot_platform: Text):
    token = token_hex(16)
    theme = {
        "title": "Orange",
    }
    flows = [
        {"id": "menu", "trigger": "/menu", "title": "Menu"},
        {"id": "features", "trigger": "/features", "title": "Features"},
        {"id": "pricing", "trigger": "/pricing", "title": "Pricing"},
        {
            "id": "about",
            "trigger": "/about",
            "title": "❔ About Us",
            "states": [
                {
                    "id": "start",
                    "actions": [
                        {
                            "message": "Acme Corp is a technology company based in Mumbai, India 🇮🇳"
                        },
                        {
                            "message": "Click the Live chat button below to connect with us and know more about the team and our products. Or you could just say a hi! 🤠",
                            "buttons": [
                                {"title": "💬 Live chat", "payload": "/livechat"},
                                {"title": "⬅️ Back", "payload": "/menu"},
                            ],
                        },
                    ],
                }
            ],
        },
        {
            "id": "livechat",
            "trigger": "/livechat",
            "title": "Live chat",
            "states": [{"id": "start", "actions": [{"custom": "livechat"}]}],
        },
    ]
    return db.bot.insert_one(
        {
            "name": bot_name,
            "platform": bot_platform,
            "flows": flows,
            "theme": theme,
            "token": token,
        },
    ).inserted_id


def _get_menu_button(button_type, bot: Dict = None):
    title = ""
    payload = f"/botmenu {button_type}"
    url = ""
    if button_type == "preview":
        title = "Preview"
        payload = ""
        token = bot.get("token")
        url = f"https://landerbot.rappo.ai?token={token}&preview=true"
    elif button_type == "edit":
        title = "Edit Bot"
    elif button_type == "settings":
        title = "Bot Settings"
    elif button_type == "delete":
        title = "Delete Bot"
    elif button_type == "backtobots":
        title = "« Back to Bots List"
    elif button_type == "bot":
        title = bot.get("name")
        payload = payload + f" {bot.get('_id')}"

    menu_button = {"title": title}
    if payload:
        menu_button["payload"] = payload
    if url:
        menu_button["url"] = url

    return menu_button


def get_mybots_menu_json_message():
    text = "Choose a bot from the list below:"
    bots = db.bot.find()
    reply_markup = {
        "keyboard": [
            [_get_menu_button("bot", b) for b in bots],
        ],
        "row_width": 2,
        "type": "inline",
    }
    return {"text": text, "reply_markup": reply_markup}


def get_edit_menu_json_message(bot_id: ObjectId):
    bot = db.bot.find_one({"_id": bot_id})
    name = bot.get("name")
    logo = "Custom" if bot.get("logo") else "Default"
    flows = ",".join([f.get("title") for f in bot.get("flows")])
    theme = get_json_key(bot, "theme.title", "Unknown")
    text = (
        f"Edit your bot.\n\nName: {name}\nLogo: {logo}\nFlows: {flows}\nTheme: {theme}"
    )
    reply_markup = {
        "keyboard": [
            [
                _get_menu_button("edit_title"),
                _get_menu_button("edit_logo"),
            ],
            [
                _get_menu_button("edit_flows"),
                _get_menu_button("edit_theme"),
            ],
        ],
        "row_width": 2,
        "type": "inline",
    }
    return {"text": text, "reply_markup": reply_markup}


def get_edit_menu_json_message(bot_id: ObjectId):
    text = ""
    bot = db.bot.find_one({"_id": bot_id})
    reply_markup = {
        "keyboard": [
            [
                _get_menu_button("edit_title"),
                _get_menu_button("edit_logo"),
            ],
            [
                _get_menu_button("edit_flows"),
                _get_menu_button("edit_theme"),
            ],
        ],
        "row_width": 2,
        "type": "inline",
    }
    return {"text": text, "reply_markup": reply_markup}


def get_bot_menu_json_message(bot_id: ObjectId, show_bots_list_button: bool = True):
    bot = db.bot.find_one({"_id": bot_id})
    text = f"Here it is: {bot.get('name')}.\nWhat do you want to do with the bot?"
    reply_markup = {
        "keyboard": [
            [
                _get_menu_button("preview"),
                _get_menu_button("edit"),
            ],
            [
                _get_menu_button("publish"),
                _get_menu_button("analytics"),
            ],
            [
                _get_menu_button("settings"),
                _get_menu_button("delete"),
            ],
        ],
        "row_width": 2,
        "type": "inline",
    }
    if show_bots_list_button:
        reply_markup["keyboard"].append(
            [
                _get_menu_button("backtobots"),
            ]
        )
    return {"text": text, "reply_markup": reply_markup}


def get_bot_json_message(
    cursor: Dict = {"view": "mybots", "show_bots_list_button": True}
):
    json_message = {}
    view = cursor.get("view", "mybots")
    show_bots_list_button = cursor.get("show_bots_list_button", True)
    bot_id = cursor.get("bot_id", None)
    if view == "mybots":
        json_message = get_mybots_menu_json_message()
    elif view == "bot":
        json_message = get_bot_menu_json_message(
            bot_id=bot_id, show_bots_list_button=show_bots_list_button
        )
    return (json_message, cursor)
