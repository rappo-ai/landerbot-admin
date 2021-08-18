from datetime import datetime
from pytz import timezone

SERVER_TZINFO = timezone("Asia/Kolkata")


def format_livechat_ts(ts):
    return datetime.fromtimestamp(ts, SERVER_TZINFO).strftime("%d-%m-%Y %H:%M:%S")
