from datetime import datetime, UTC
from agents import function_tool

@function_tool
def get_datetime_now():
    return datetime.now(UTC) 