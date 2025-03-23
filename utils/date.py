from datetime import datetime
from agents import function_tool
from dateutil import parser
import pytz

@function_tool()
async def current_time(timezone: str = None) -> str:
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