from datetime import datetime
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from actions.utils.admin_config import get_admin_group_id
from actions.utils.csv import format_csv_entry
from actions.utils.date import SERVER_TZINFO
from actions.utils.entity import get_entity
from actions.utils.json import get_json_key
from actions.utils.livechat import get_livechats
from actions.utils.menu import (
    DATE_SELECTOR_DISPLAY_NAME,
    LIFECYCLE_SELECTOR_DISPLAY_NAME,
    LIFECYCLE_SELECTOR_STAGE_MAP,
    VIEW_SELECTOR_COMMAND,
    VIEW_SELECTOR_DATE,
    VIEW_SELECTOR_LIFECYCLE,
    get_date_picker,
    get_lifecycle_picker,
    get_timestamps,
)


def format_chat_header_for_csv():
    cols = [
        "Chat ID",
        "Creation Timestamp",
        "Last Update Timestamp",
        "User ID",
        "User Name",
        "User Email",
        "City",
        "Country",
        "Lead Status",
        "Device Name",
        "Form Factor",
        "Browser Name",
        "Browser Version",
        "Referrer Url",
        "Sessions",
    ]
    return ",".join(cols)


def format_chat_for_csv(c):
    cols = [
        f"{get_json_key(c, '_id')}",
        f"{get_json_key(c, 'creation_ts')}",
        f"{get_json_key(c, 'last_update_ts')}",
        f"{get_json_key(c, 'user_id')}",
        format_csv_entry(f"{get_json_key(c, 'user_metadata.user_name')}"),
        format_csv_entry(f"{get_json_key(c, 'user_metadata.user_email')}"),
        format_csv_entry(f"{get_json_key(c, 'user_metadata.location_data.city')}"),
        format_csv_entry(f"{get_json_key(c, 'user_metadata.location_data.country')}"),
        format_csv_entry(f"{get_json_key(c, 'user_metadata.lifecycle_stage')}"),
        format_csv_entry(
            f"{get_json_key(c, 'user_metadata.wurfl_data.complete_device_name')}"
        ),
        format_csv_entry(f"{get_json_key(c, 'user_metadata.wurfl_data.form_factor')}"),
        format_csv_entry(
            f"{get_json_key(c, 'user_metadata.browser_data.browserName')}"
        ),
        format_csv_entry(
            f"{get_json_key(c, 'user_metadata.browser_data.fullVersion')}"
        ),
        format_csv_entry(f"{get_json_key(c, 'user_metadata.referrer_data.referrer')}"),
        f"{len(c.get('sessions', []))}",
    ]
    return ",".join(cols)


def export_users(lifecycle_selector, date_selector):
    lifecycle_stage = LIFECYCLE_SELECTOR_STAGE_MAP.get(lifecycle_selector, None)

    current_from_ts, current_to_ts, previous_from_ts, previous_to_ts = get_timestamps(
        date_selector
    )

    livechats = get_livechats(
        lifecycle_stage=lifecycle_stage, from_ts=current_from_ts, to_ts=current_to_ts
    )

    chat_count = livechats.count()

    lifecycle_stage_name = lifecycle_stage or "all"
    date_selector_name = DATE_SELECTOR_DISPLAY_NAME.get(date_selector)
    current_date = datetime.now(tz=SERVER_TZINFO)
    current_date_str = current_date.strftime("%d.%m.%y_%H.%M_%p")
    file_name_base = f"{lifecycle_stage_name}_{date_selector_name.replace(' ', '-')}_{current_date_str}"
    file_name_csv = f"{file_name_base}.csv"
    chats_csv_list = [format_chat_header_for_csv()] if chat_count else []
    for c in livechats:
        chats_csv_list.append(format_chat_for_csv(c))
    chats_csv = "\n".join(chats_csv_list)

    text = ""

    selection = f"({LIFECYCLE_SELECTOR_DISPLAY_NAME.get(lifecycle_selector)}, {DATE_SELECTOR_DISPLAY_NAME.get(date_selector)})"
    if chat_count:
        text += f"Exported data of {chat_count} chats {selection} as CSV file."
    else:
        text += f"No chats to export for the given selection {selection}."

    return (
        text,
        chats_csv,
        file_name_csv,
        {
            "text": text,
            "reply_markup": {
                "keyboard": [
                    [
                        {
                            "title": "Back",
                            "payload": f'/export{{"v":"{VIEW_SELECTOR_DATE}","l":"{lifecycle_selector}"}}',
                        },
                    ],
                ],
                "type": "inline",
            },
        },
    )


class ActionExport(Action):
    def name(self) -> Text:
        return "action_export"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        entities = tracker.latest_message.get("entities", [])
        view_selector = get_entity(entities, "v", VIEW_SELECTOR_LIFECYCLE)
        lifecycle_selector = get_entity(entities, "l")
        date_selector = get_entity(entities, "d")

        metadata = tracker.latest_message.get("metadata", {})
        callback_query_message = get_json_key(metadata, "callback_query.message", {})
        callback_query_message_id = callback_query_message.get("message_id")

        json_message = {}
        if view_selector == VIEW_SELECTOR_LIFECYCLE:
            json_message = get_lifecycle_picker(
                "/export", "Select whose data you want to export:"
            )
        elif view_selector == VIEW_SELECTOR_DATE:
            json_message = get_date_picker(
                "/export",
                f"Select the date range for {LIFECYCLE_SELECTOR_DISPLAY_NAME[lifecycle_selector]} export:",
                lifecycle_selector,
            )
        elif view_selector == VIEW_SELECTOR_COMMAND:
            (caption, csv_data, csv_filename, json_message) = export_users(
                lifecycle_selector, date_selector
            )
            if csv_data:
                dispatcher.utter_message(
                    json_message={
                        "caption": caption,
                        "document": csv_data,
                        "document_file_type": "text/csv",
                        "document_file_name": csv_filename,
                    }
                )

        if json_message:
            if callback_query_message_id:
                json_message["message_id"] = callback_query_message_id
                json_message["chat_id"] = get_admin_group_id()
            dispatcher.utter_message(json_message=json_message)

        return []
