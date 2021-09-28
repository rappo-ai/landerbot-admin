from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from actions.utils.date import SERVER_TZINFO

LIFECYCLE_SELECTOR_ALL = "a"
LIFECYCLE_SELECTOR_QUALIFIED = "q"
LIFECYCLE_SELECTOR_UNQUALIFIED = "u"

LIFECYCLE_SELECTOR_DISPLAY_NAME = {
    LIFECYCLE_SELECTOR_ALL: "🔷 All",
    LIFECYCLE_SELECTOR_QUALIFIED: "✅ Qualified Lead",
    LIFECYCLE_SELECTOR_UNQUALIFIED: "❌ Unqualified",
}

LIFECYCLE_SELECTOR_STAGE_MAP = {
    LIFECYCLE_SELECTOR_ALL: None,
    LIFECYCLE_SELECTOR_QUALIFIED: "lead",
    LIFECYCLE_SELECTOR_UNQUALIFIED: "unqualified",
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

VIEW_SELECTOR_COMMAND = "s"
VIEW_SELECTOR_DATE = "d"
VIEW_SELECTOR_LIFECYCLE = "l"


def get_lifecycle_picker(command, text):
    return {
        "text": text,
        "reply_markup": {
            "keyboard": [
                [
                    {
                        "title": LIFECYCLE_SELECTOR_DISPLAY_NAME[
                            LIFECYCLE_SELECTOR_QUALIFIED
                        ],
                        "payload": f'{command}{{"v":"{VIEW_SELECTOR_DATE}","l":"{LIFECYCLE_SELECTOR_QUALIFIED}"}}',
                    },
                    {
                        "title": LIFECYCLE_SELECTOR_DISPLAY_NAME[
                            LIFECYCLE_SELECTOR_UNQUALIFIED
                        ],
                        "payload": f'{command}{{"v":"{VIEW_SELECTOR_DATE}","l":"{LIFECYCLE_SELECTOR_UNQUALIFIED}"}}',
                    },
                ],
                [
                    {
                        "title": LIFECYCLE_SELECTOR_DISPLAY_NAME[
                            LIFECYCLE_SELECTOR_ALL
                        ],
                        "payload": f'{command}{{"v":"{VIEW_SELECTOR_DATE}","l":"{LIFECYCLE_SELECTOR_ALL}"}}',
                    },
                ],
            ],
            "type": "inline",
        },
    }


def get_date_picker(command, text, lifecycle_selector):
    return {
        "text": text,
        "reply_markup": {
            "keyboard": [
                [
                    {
                        "title": "Today",
                        "payload": f'{command}{{"v":"{VIEW_SELECTOR_COMMAND}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_TODAY}"}}',
                    },
                    {
                        "title": "Yesterday",
                        "payload": f'{command}{{"v":"{VIEW_SELECTOR_COMMAND}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_YESTERDAY}"}}',
                    },
                ],
                [
                    {
                        "title": "This Week",
                        "payload": f'{command}{{"v":"{VIEW_SELECTOR_COMMAND}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_THIS_WEEK}"}}',
                    },
                    {
                        "title": "Last Week",
                        "payload": f'{command}{{"v":"{VIEW_SELECTOR_COMMAND}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_LAST_WEEK}"}}',
                    },
                ],
                [
                    {
                        "title": "This Month",
                        "payload": f'{command}{{"v":"{VIEW_SELECTOR_COMMAND}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_THIS_MONTH}"}}',
                    },
                    {
                        "title": "Last Month",
                        "payload": f'{command}{{"v":"{VIEW_SELECTOR_COMMAND}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_LAST_MONTH}"}}',
                    },
                ],
                [
                    {
                        "title": "This Year",
                        "payload": f'{command}{{"v":"{VIEW_SELECTOR_COMMAND}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_THIS_YEAR}"}}',
                    },
                    {
                        "title": "Last Year",
                        "payload": f'{command}{{"v":"{VIEW_SELECTOR_COMMAND}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_LAST_YEAR}"}}',
                    },
                ],
                [
                    {
                        "title": "All Time",
                        "payload": f'{command}{{"v":"{VIEW_SELECTOR_COMMAND}","l":"{lifecycle_selector}","d":"{DATE_SELECTOR_ALL_TIME}"}}',
                    },
                    {
                        "title": "Back",
                        "payload": f'{command}{{"v":"{VIEW_SELECTOR_LIFECYCLE}"}}',
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
