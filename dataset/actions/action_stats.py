from collections import Counter
from copy import deepcopy
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from actions.utils.admin_config import get_admin_group_id
from actions.utils.date import SERVER_TZINFO, to_readable_duration
from actions.utils.entity import get_entity
from actions.utils.json import get_json_key
from actions.utils.livechat import get_livechat_stats

LIFECYCLE_SELECTOR_ALL = "a"
LIFECYCLE_SELECTOR_QUALIFIED = "q"
LIFECYCLE_SELECTOR_UNQUALIFIED = "u"

LIFECYCLE_SELECTOR_DISPLAY_NAME = {
    LIFECYCLE_SELECTOR_ALL: "🔷 All",
    LIFECYCLE_SELECTOR_QUALIFIED: "✅ Qualified Lead",
    LIFECYCLE_SELECTOR_UNQUALIFIED: "❌ Unqualified",
}

DATE_SELECTOR_TODAY = "t"
DATE_SELECTOR_YESTERDAY = "s"
DATE_SELECTOR_THIS_WEEK = "w"
DATE_SELECTOR_LAST_WEEK = "v"
DATE_SELECTOR_THIS_MONTH = "m"
DATE_SELECTOR_LAST_MONTH = "l"
DATE_SELECTOR_THIS_YEAR = "y"
DATE_SELECTOR_LAST_YEAR = "x"
DATE_SELECTOR_ALL_TIME = "a"

DATE_SELECTOR_DISPLAY_NAME = {
    DATE_SELECTOR_TODAY: "Today",
    DATE_SELECTOR_YESTERDAY: "Yesterday",
    DATE_SELECTOR_THIS_WEEK: "This Week",
    DATE_SELECTOR_LAST_WEEK: "Last Week",
    DATE_SELECTOR_THIS_MONTH: "This Month",
    DATE_SELECTOR_LAST_MONTH: "Last Month",
    DATE_SELECTOR_THIS_YEAR: "This Year",
    DATE_SELECTOR_LAST_YEAR: "Last Year",
    DATE_SELECTOR_ALL_TIME: "All Time",
}

VIEW_SELECTOR_LIFECYCLE = "l"
VIEW_SELECTOR_DATE = "d"
VIEW_SELECTOR_STATS = "s"


def get_lifecycle_picker():
    return {
        "text": "Select whose stats you want to see:",
        "reply_markup": {
            "keyboard": [
                [
                    {
                        "title": LIFECYCLE_SELECTOR_DISPLAY_NAME[
                            LIFECYCLE_SELECTOR_QUALIFIED
                        ],
                        "payload": f'/stats{{"v":"{VIEW_SELECTOR_DATE}","l":"{LIFECYCLE_SELECTOR_QUALIFIED}"}}',
                    },
                    {
                        "title": LIFECYCLE_SELECTOR_DISPLAY_NAME[
                            LIFECYCLE_SELECTOR_UNQUALIFIED
                        ],
                        "payload": f'/stats{{"v":"{VIEW_SELECTOR_DATE}","l":"{LIFECYCLE_SELECTOR_UNQUALIFIED}"}}',
                    },
                ],
                [
                    {
                        "title": LIFECYCLE_SELECTOR_DISPLAY_NAME[
                            LIFECYCLE_SELECTOR_ALL
                        ],
                        "payload": f'/stats{{"v":"{VIEW_SELECTOR_DATE}","l":"{LIFECYCLE_SELECTOR_ALL}"}}',
                    },
                ],
            ],
            "type": "inline",
        },
    }


def get_date_picker(lifecycle_selector):
    return {
        "text": f"Select the date range for {LIFECYCLE_SELECTOR_DISPLAY_NAME[lifecycle_selector]} stats:",
        "reply_markup": {
            "keyboard": [
                [
                    {
                        "title": "Today",
                        "payload": f'/stats{{"v":"{VIEW_SELECTOR_STATS}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_TODAY}"}}',
                    },
                    {
                        "title": "Yesterday",
                        "payload": f'/stats{{"v":"{VIEW_SELECTOR_STATS}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_YESTERDAY}"}}',
                    },
                ],
                [
                    {
                        "title": "This Week",
                        "payload": f'/stats{{"v":"{VIEW_SELECTOR_STATS}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_THIS_WEEK}"}}',
                    },
                    {
                        "title": "Last Week",
                        "payload": f'/stats{{"v":"{VIEW_SELECTOR_STATS}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_LAST_WEEK}"}}',
                    },
                ],
                [
                    {
                        "title": "This Month",
                        "payload": f'/stats{{"v":"{VIEW_SELECTOR_STATS}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_THIS_MONTH}"}}',
                    },
                    {
                        "title": "Last Month",
                        "payload": f'/stats{{"v":"{VIEW_SELECTOR_STATS}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_LAST_MONTH}"}}',
                    },
                ],
                [
                    {
                        "title": "This Year",
                        "payload": f'/stats{{"v":"{VIEW_SELECTOR_STATS}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_THIS_YEAR}"}}',
                    },
                    {
                        "title": "Last Year",
                        "payload": f'/stats{{"v":"{VIEW_SELECTOR_STATS}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_LAST_YEAR}"}}',
                    },
                ],
                [
                    {
                        "title": "All Time",
                        "payload": f'/stats{{"v":"{VIEW_SELECTOR_STATS}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_ALL_TIME}"}}',
                    },
                    {
                        "title": "Back",
                        "payload": f'/stats{{"v":"{VIEW_SELECTOR_LIFECYCLE}"}}',
                    },
                ],
            ],
            "type": "inline",
        },
    }


def get_timestamps(date_selector):
    now_dt = datetime.now(tz=SERVER_TZINFO)
    today_dt = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    this_week_dt = today_dt - timedelta(days=now_dt.weekday())
    this_month_dt = today_dt.replace(day=1)
    this_year_dt = today_dt.replace(month=1, day=1)

    if date_selector == DATE_SELECTOR_TODAY:
        return (
            today_dt.timestamp(),
            (today_dt + timedelta(days=1)).timestamp(),
            (today_dt - timedelta(days=1)).timestamp(),
            today_dt.timestamp(),
        )
    elif date_selector == DATE_SELECTOR_YESTERDAY:
        return (
            (today_dt - timedelta(days=1)).timestamp(),
            today_dt.timestamp(),
            (today_dt - timedelta(days=2)).timestamp(),
            (today_dt - timedelta(days=1)).timestamp(),
        )
    elif date_selector == DATE_SELECTOR_THIS_WEEK:
        return (
            this_week_dt.timestamp(),
            (this_week_dt + timedelta(days=7)).timestamp(),
            (this_week_dt - timedelta(days=7)).timestamp(),
            this_week_dt.timestamp(),
        )
    elif date_selector == DATE_SELECTOR_LAST_WEEK:
        return (
            (this_week_dt - timedelta(days=7)).timestamp(),
            this_week_dt.timestamp(),
            (this_week_dt - timedelta(days=14)).timestamp(),
            (this_week_dt - timedelta(days=7)).timestamp(),
        )
    elif date_selector == DATE_SELECTOR_THIS_MONTH:
        return (
            this_month_dt.timestamp(),
            (this_month_dt + relativedelta(months=1)).timestamp(),
            (this_month_dt - relativedelta(months=1)).timestamp(),
            this_month_dt.timestamp(),
        )
    elif date_selector == DATE_SELECTOR_LAST_MONTH:
        return (
            (this_month_dt - relativedelta(months=1)).timestamp(),
            this_month_dt.timestamp(),
            (this_month_dt - relativedelta(months=2)).timestamp(),
            (this_month_dt - relativedelta(months=1)).timestamp(),
        )
    elif date_selector == DATE_SELECTOR_THIS_YEAR:
        return (
            this_year_dt.timestamp(),
            (this_year_dt + relativedelta(years=1)).timestamp(),
            (this_year_dt - relativedelta(years=1)).timestamp(),
            this_year_dt.timestamp(),
        )
    elif date_selector == DATE_SELECTOR_LAST_YEAR:
        return (
            (this_year_dt - relativedelta(years=1)).timestamp(),
            this_year_dt.timestamp(),
            (this_year_dt - relativedelta(years=2)).timestamp(),
            (this_year_dt - relativedelta(years=1)).timestamp(),
        )
    return (None, None, None, None)


def diff_livechat_stats(livechat_stats, previous_livechat_stats):
    out_stats = deepcopy(livechat_stats)

    def compute_diffs(source, previous_source, source_key):
        for key, value in source.items():
            previous_value = previous_source.get(key)
            if previous_value is None:
                continue
            diff = value - previous_value
            out_stats[source_key]["diffs"][key] = diff
            if previous_value:
                out_stats[source_key]["diff_percents"][key] = (
                    (value - previous_value) / previous_value
                ) * 100

    if out_stats.get("funnel"):
        out_stats["funnel"]["diffs"] = {}
        out_stats["funnel"]["diff_percents"] = {}
        funnel = livechat_stats.get("funnel", {})
        previous_funnel = previous_livechat_stats.get("funnel", {})
        compute_diffs(funnel, previous_funnel, "funnel")

    if out_stats.get("averages"):
        out_stats["averages"]["diffs"] = {}
        out_stats["averages"]["diff_percents"] = {}
        averages = livechat_stats.get("averages", {})
        previous_averages = previous_livechat_stats.get("averages", {})
        compute_diffs(averages, previous_averages, "averages")

    return out_stats


def get_stats(lifecycle_selector, date_selector):
    lifecycle_stage = {
        LIFECYCLE_SELECTOR_ALL: None,
        LIFECYCLE_SELECTOR_QUALIFIED: "lead",
        LIFECYCLE_SELECTOR_UNQUALIFIED: "unqualified",
    }.get(lifecycle_selector, None)

    current_from_ts, current_to_ts, previous_from_ts, previous_to_ts = get_timestamps(
        date_selector
    )

    livechat_stats = get_livechat_stats(
        lifecycle_stage=lifecycle_stage, from_ts=current_from_ts, to_ts=current_to_ts
    )
    if date_selector != DATE_SELECTOR_ALL_TIME:
        previous_livechat_stats = get_livechat_stats(
            lifecycle_stage=lifecycle_stage,
            from_ts=previous_from_ts,
            to_ts=previous_to_ts,
        )
        livechat_stats = diff_livechat_stats(livechat_stats, previous_livechat_stats)

    text = ""

    text += f"Stats for {LIFECYCLE_SELECTOR_DISPLAY_NAME.get(lifecycle_selector)} for {DATE_SELECTOR_DISPLAY_NAME.get(date_selector)}:\n\n"

    def get_arrow(val):
        return "🔼 " if val and val > 0 else ("🔽 " if val and val < 0 else "")

    def get_stat_title(key):
        STAT_TITLES = {
            "total_users": "Total Users",
            "new_users": "New Users",
            "returning_users": "Returning Users",
            "widget_open": "Widget Open",
            "pricing": "Pricing",
            "features": "Features",
            "installation": "Installation",
            "about": "About",
            "contact": "Contact",
            "live_chat_enabled": "Live Chat Enabled",
            "subscribe": "Subscribe",
            "qualified_lead": "Qualified Leads",
            "unqualified": "Unqualified",
            "untagged": "Untagged",
            "sessions_per_user": "Avg. Sessions per User",
            "session_duration": "Avg. Session Duration",
            "cities": "Top Cities",
            "countries": "Top Countries",
            "form_factors": "Top Form Factors",
            "devices": "Top Devices",
            "browsers": "Top Browsers",
            "referrers": "Top Referrers",
        }
        return STAT_TITLES.get(key, "?")

    def print_value_with_diff(key, value, diff, title):
        arrow = get_arrow(diff)
        diff_str = (
            ""
            if not diff or date_selector == DATE_SELECTOR_ALL_TIME
            else f" ({arrow}{round(diff)}%)"
        )
        if key == "session_duration":
            value = to_readable_duration(value)
        elif key == "sessions_per_user":
            value = round(value, 2)
        return f"{title}: {value}{diff_str}\n"

    def print_most_common_from_list(input_list, n, title):
        total = len(input_list)
        if not total:
            return ""
        c = Counter(input_list)
        most_common_list = c.most_common(n)
        return f"{title}: {', '.join([v[0] + ' (' + str(round((v[1]/total)*100)) + '%)' for v in most_common_list])}\n"

    funnel_diff_percents = get_json_key(livechat_stats, "funnel.diff_percents", {})
    for key, value in livechat_stats.get("funnel", {}).items():
        if key in ["diffs", "diff_percents"]:
            continue
        text += print_value_with_diff(
            key,
            value,
            funnel_diff_percents.get(key),
            get_stat_title(key),
        )

    text += "\n"
    averages_diff_percents = get_json_key(livechat_stats, "averages.diff_percents", {})
    for key, value in livechat_stats.get("averages", {}).items():
        if key in ["diffs", "diff_percents"]:
            continue
        text += print_value_with_diff(
            key,
            value,
            averages_diff_percents.get(key),
            get_stat_title(key),
        )

    text += "\n"
    for key, value in livechat_stats.get("lists", {}).items():
        if key in ["diffs", "diff_percents"]:
            continue
        text += print_most_common_from_list(value, 5, get_stat_title(key))

    return {
        "text": text,
        "reply_markup": {
            "keyboard": [
                [
                    {
                        "title": "Back",
                        "payload": f'/stats{{"v":"{VIEW_SELECTOR_DATE}","l":"{lifecycle_selector}"}}',
                    },
                ],
            ],
            "type": "inline",
        },
        "disable_web_page_preview": True,
    }


class ActionStats(Action):
    def name(self) -> Text:
        return "action_stats"

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
            json_message = get_lifecycle_picker()
        elif view_selector == VIEW_SELECTOR_DATE:
            json_message = get_date_picker(lifecycle_selector)
        elif view_selector == VIEW_SELECTOR_STATS:
            json_message = get_stats(lifecycle_selector, date_selector)

        if json_message:
            if callback_query_message_id:
                json_message["message_id"] = callback_query_message_id
                json_message["chat_id"] = get_admin_group_id()
            dispatcher.utter_message(json_message=json_message)

        return []
