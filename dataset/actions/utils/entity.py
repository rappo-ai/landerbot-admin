from typing import Any, List, Text


def get_entity(entities: List, name: Text, default: Any = None):
    return next(
        iter([e.get("value") for e in entities if e.get("entity") == name]), default
    )
