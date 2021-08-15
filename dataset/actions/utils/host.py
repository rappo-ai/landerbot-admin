import logging
from ruamel import yaml
from typing import Dict, Optional, Text

logger = logging.getLogger(__name__)


def get_host_url(path: Optional[Text] = ""):
    with open("credentials.yml", "r") as stream:
        try:
            credentials: Dict = yaml.safe_load(stream)
            telegram_credentials: Dict = credentials.get(
                "connectors.telegram.TelegramInput", {}
            )
            return telegram_credentials.get("host_url", "") + path
        except Exception as exc:
            logger.error(exc)
