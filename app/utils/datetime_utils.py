import datetime

def get_today_range_kst():
    KST = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(KST)
    start = now - datetime.timedelta(hours=12)
    end = now
    return start, end