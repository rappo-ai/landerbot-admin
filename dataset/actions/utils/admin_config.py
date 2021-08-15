from typing import List, Text
from bson.objectid import ObjectId

from actions.db.store import db
from actions.utils.debug import is_debug_env

ADMIN_CONFID_OBJECT_ID = "000000000000000000000001"


def lazy_init():
    admin_config = db.admin_config.find_one({"_id": ObjectId(ADMIN_CONFID_OBJECT_ID)})
    if not admin_config:
        db.admin_config.insert_one(
            {
                "_id": ObjectId(ADMIN_CONFID_OBJECT_ID),
                "super_admins": [],
                "admin_group_id": "",
            },
        )


def is_super_admin(chat_id: Text):
    if is_debug_env():
        return True
    return chat_id in get_super_admins()


def is_admin_group(chat_id: Text):
    return get_admin_group_id() == chat_id


def get_super_admins():
    lazy_init()
    return db.admin_config.find_one({"_id": ObjectId(ADMIN_CONFID_OBJECT_ID)}).get(
        "super_admins"
    )


def get_admin_group_id():
    lazy_init()
    return db.admin_config.find_one({"_id": ObjectId(ADMIN_CONFID_OBJECT_ID)}).get(
        "admin_group_id"
    )


def set_admin_group_id(group_id):
    lazy_init()
    db.admin_config.update_one(
        {"_id": ObjectId(ADMIN_CONFID_OBJECT_ID)},
        {"$set": {"admin_group_id": group_id}},
    )
