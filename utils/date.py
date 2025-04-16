from datetime import datetime
from agents import function_tool
from dateutil import parser
import pytz
from tzlocal import get_localzone

@function_tool()
async def current_time(timezone: str = None) -> str:
    try:
        if timezone is None: timezone = "Asia/Ho_Chi_Minh"
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        return str(current_time.isoformat())
    except pytz.UnknownTimeZoneError:
        return "Múi giờ không hợp lệ"
    
def current_time_v2(timezone: str = None) -> str:
    try:
        if timezone is None: timezone = "Asia/Ho_Chi_Minh"
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        return str(current_time.isoformat())
    except pytz.UnknownTimeZoneError:
        return "Múi giờ không hợp lệ"
    
def convert_date(data):
    if isinstance(data, dict):  # Nếu là dict, duyệt từng key
        return {k: convert_date(v) for k, v in data.items()}
    elif isinstance(data, list):  # Nếu là list, duyệt từng phần tử
        return [convert_date(item) for item in data]
    elif isinstance(data, str):  # Nếu là chuỗi, thử parse datetime
        try:
            return parser.parse(data)
        except (ValueError, TypeError):  # Nếu không phải datetime, giữ nguyên
            return data
    else:
        return data

def convert_to_local_timezone(data, as_string=True, format_str="%Y-%m-%d %H:%M:%S %z"):
    """
    Recursively convert all datetime objects in a data structure to the local timezone.
    
    Args:
        data: Input data (dict, list, datetime, or other).
        as_string: If True, returns datetimes as formatted strings; if False, returns datetime objects.
        format_str: Format for string output (used only if as_string=True).
    
    Returns:
        Data with all datetime objects converted to the local timezone.
    """
    # Get the local timezone
    local_tz = get_localzone()
    utc_tz = pytz.UTC

    if isinstance(data, dict):
        return {k: convert_to_local_timezone(v, as_string, format_str) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_to_local_timezone(item, as_string, format_str) for item in data]
    elif isinstance(data, datetime):
        if data.tzinfo is None:
            data = utc_tz.localize(data)
        local_dt = data.astimezone(local_tz)
        return local_dt.strftime(format_str) if as_string else local_dt
    else: 
        return data