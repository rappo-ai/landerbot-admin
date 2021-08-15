from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, EventType
from rasa_sdk.executor import CollectingDispatcher

from actions.utils.admin_config import get_admin_group_id
from actions.utils.json import get_json_key
from actions.utils.markdown import escape_markdown, get_user_link
from actions.utils.telegram import get_chat_type, get_first_name, get_user_id


class ActionSessionStart(Action):
    def name(self) -> Text:
        return "action_session_start"

    @staticmethod
    def fetch_previous_slots(tracker: Tracker) -> List[EventType]:
        """Collect all prior slots"""

        slots = []
        for key in tracker.slots.keys():
            value = tracker.get_slot(key)
            if (value is not None) and (key != "session_started_metadata"):
                slots.append(SlotSet(key=key, value=value))
        return slots

    @staticmethod
    def fetch_telegram_slots(tracker: Tracker) -> List[EventType]:
        """Add Telegram-specific slots"""

        metadata = tracker.get_slot("session_started_metadata")

        slots = []

        chat_type = get_chat_type(metadata)
        if chat_type is not None:
            slots.append(SlotSet(key="chat_type", value=chat_type))

        first_name = get_first_name(metadata)
        if first_name is not None:
            slots.append(SlotSet(key="first_name", value=first_name))

        telegram_user_id = get_user_id(metadata)
        if telegram_user_id is not None:
            slots.append(SlotSet(key="telegram_user_id", value=str(telegram_user_id)))

        return slots

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # the session should begin with a `session_started` event
        events = [SessionStarted()]

        # any slots that should be carried over should come after the
        # `session_started` event
        if get_json_key(domain, "session_config.carry_over_slots_to_new_session", True):
            events.extend(self.fetch_previous_slots(tracker))

        # add slots specific to Telegram platform
        if tracker.get_latest_input_channel() == "telegram":
            events.extend(self.fetch_telegram_slots(tracker))

        # an `action_listen` should be added at the end as a user message follows
        events.append(ActionExecuted("action_listen"))

        return events
