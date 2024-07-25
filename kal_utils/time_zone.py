from datetime import datetime
import pytz

def parse_date_str(date_str):
    if date_str:
        return datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
    return datetime.min

def get_time_israel():
    israel_tz = pytz.timezone('Asia/Jerusalem')
    israel_time = datetime.now(israel_tz)
    return israel_time.strftime("%d/%m/%Y %H:%M:%S")

def get_time_new_york():
    new_york_tz = pytz.timezone('America/New_York')
    new_york_time = datetime.now(new_york_tz)
    return new_york_time.strftime("%d/%m/%Y %H:%M:%S")

def get_time_chicago():
    chicago_tz = pytz.timezone('America/Chicago')
    chicago_time = datetime.now(chicago_tz)
    return chicago_time.strftime("%d/%m/%Y %H:%M:%S")

def get_time_los_angeles():
    los_angeles_tz = pytz.timezone('America/Los_Angeles')
    los_angeles_time = datetime.now(los_angeles_tz)
    return los_angeles_time.strftime("%d/%m/%Y %H:%M:%S")

def get_time_london():
    london_tz = pytz.timezone('Europe/London')
    london_time = datetime.now(london_tz)
    return london_time.strftime("%d/%m/%Y %H:%M:%S")

def get_time_paris():
    paris_tz = pytz.timezone('Europe/Paris')
    paris_time = datetime.now(paris_tz)
    return paris_time.strftime("%d/%m/%Y %H:%M:%S")

def get_time_berlin():
    berlin_tz = pytz.timezone('Europe/Berlin')
    berlin_time = datetime.now(berlin_tz)
    return berlin_time.strftime("%d/%m/%Y %H:%M:%S")

def get_time_tokyo():
    tokyo_tz = pytz.timezone('Asia/Tokyo')
    tokyo_time = datetime.now(tokyo_tz)
    return tokyo_time.strftime("%d/%m/%Y %H:%M:%S")

def get_time_beijing():
    beijing_tz = pytz.timezone('Asia/Shanghai')
    beijing_time = datetime.now(beijing_tz)
    return beijing_time.strftime("%d/%m/%Y %H:%M:%S")

def get_time_delhi():
    delhi_tz = pytz.timezone('Asia/Kolkata')
    delhi_time = datetime.now(delhi_tz)
    return delhi_time.strftime("%d/%m/%Y %H:%M:%S")
