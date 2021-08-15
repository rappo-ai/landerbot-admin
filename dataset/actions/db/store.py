from pymongo.database import Database
from typing import Optional, Text


class MongoDataStore:
    """Stores data in Mongo.

    Property methods:
        conversations: returns the current conversation
    """

    def __init__(
        self,
        host: Optional[Text] = "mongodb://mongo:27017",
        db: Optional[Text] = "rappo",
        username: Optional[Text] = None,
        password: Optional[Text] = None,
        auth_source: Optional[Text] = "admin",
    ) -> None:
        from pymongo import MongoClient

        self.client = MongoClient(
            host,
            username=username,
            password=password,
            authSource=auth_source,
        )

        self.db = Database(self.client, db)


_db_store = MongoDataStore()

db = _db_store.db


def reset_actions_db():
    for c in db.list_collection_names():
        db.drop_collection(c)
