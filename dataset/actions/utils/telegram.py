import logging
from ruamel import yaml
from typing import Dict

from actions.utils.json import get_json_key

logger = logging.getLogger(__name__)


def get_chat_type(metadata):
    return get_json_key(metadata, "message.chat.type") or get_json_key(
        metadata, "callback_query.message.chat.type"
    )


def get_first_name(metadata):
    return get_json_key(metadata, "message.from.first_name") or get_json_key(
        metadata, "callback_query.from.first_name"
    )

def get_user_id(metadata):
    return get_json_key(metadata, "message.from.id") or get_json_key(
        metadata, "callback_query.from.id"
    )

def get_bot_token():
    with open("credentials.yml", "r") as stream:
        try:
            credentials: Dict = yaml.safe_load(stream)
            telegram_credentials: Dict = credentials.get(
                "connectors.telegram.TelegramInput", {}
            )
            return telegram_credentials.get("access_token", "")
        except Exception as exc:
            logger.error(exc)
