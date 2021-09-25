from datetime import datetime
from dateutil.relativedelta import relativedelta
from pytz import timezone

SERVER_TZINFO = timezone("Asia/Kolkata")


def format_livechat_ts(ts):
    return datetime.fromtimestamp(ts, SERVER_TZINFO).strftime("%d-%m-%Y %H:%M:%S")


def to_readable_duration(duration_ts):
    rd = relativedelta(seconds=duration_ts)
    readable_duration = ""
    if rd.years:
        readable_duration += ", " if readable_duration else ""
        readable_duration += f"{round(rd.years)} years"
    if rd.months:
        readable_duration += ", " if readable_duration else ""
        readable_duration += f"{round(rd.months)} months"
    if rd.days:
        readable_duration += ", " if readable_duration else ""
        readable_duration += f"{round(rd.days)} days"
    if rd.hours:
        readable_duration += ", " if readable_duration else ""
        readable_duration += f"{round(rd.hours)} hours"
    if rd.minutes:
        readable_duration += ", " if readable_duration else ""
        readable_duration += f"{round(rd.minutes)} minutes"
    if rd.seconds:
        readable_duration += ", " if readable_duration else ""
        readable_duration += f"{round(rd.seconds)} seconds"
    return readable_duration
