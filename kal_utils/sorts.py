from datetime import datetime
from .time_zone import parse_date_str

def get_field_value(obj, field):
    if isinstance(obj, dict):
        return obj.get(field, None)
    return getattr(obj, field, None)

def sort_by_date(data, field):
    return sorted(data, key=lambda obj: parse_date_str(get_field_value(obj, field)), reverse=True)
