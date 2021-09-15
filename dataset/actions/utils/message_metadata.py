import logging
from typing import Dict

from actions.db.store import db


logger = logging.getLogger(__name__)

db.message_metadata.create_index("message_id")


def get_message_metadata(
    message_id,
):
    return db.message_metadata.find_one({"message_id": message_id})


def set_message_metadata(
    message_id,
    metadata: Dict,
):
    db.message_metadata.update_one(
        {"message_id": message_id},
        {"$set": metadata},
        upsert=True,
    )
