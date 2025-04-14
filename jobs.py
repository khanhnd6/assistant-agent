import logging
from datetime import datetime, timedelta
from utils.database import MongoDBConnection
from utils.telegram import async_send_message
from datetime import datetime, timezone
from collections import defaultdict
import asyncio
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.background import BackgroundScheduler

from dotenv import load_dotenv
load_dotenv()


def format_value(value):
    """Format special values like dates"""
    if isinstance(value, dict):
        if "$date" in value:
            try:
                dt = datetime.fromisoformat(value["$date"].replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                return value["$date"]
        return str(value)
    return str(value)

def get_schema_map(schemas):
    """Create a mapping of schema_name to field display names"""
    schema_map = {}
    for schema in schemas:
        field_map = {field["name"]: field["display_name"] for field in schema["fields"]}
        schema_map[schema["name"]] = {
            "display_name": schema["display_name"],
            "fields": field_map
        }
    return schema_map

def generate_user_messages(records, schemas):
    """Generate a list of (user_id, message) tuples with only schema fields"""
    schema_map = get_schema_map(schemas)
    grouped = defaultdict(lambda: defaultdict(list))

    # Group records by user_id and schema_name
    for record in records:
        user_id = record["_user_id"]
        schema_name = record["_schema_name"]
        grouped[user_id][schema_name].append(record)

    # Generate messages
    messages = []
    for user_id, schemas_data in grouped.items():
        message_lines = [f" 🔔 Reminder Notification 🔔 "]
        
        for schema_name, records_list in schemas_data.items():
            if schema_name in schema_map:
                schema_display = schema_map[schema_name]["display_name"]
                message_lines.append(f"\n{schema_display}:")
                
                for i, record in enumerate(records_list, 1):
                    message_lines.append(f"\nItem #{i}:")
                    field_map = schema_map[schema_name]["fields"]
                    for key, value in record.items():
                        if key in field_map:
                            display_name = field_map[key]
                            formatted_value = format_value(value)
                            message_lines.append(f" * {display_name}: {formatted_value}")
        
        messages.append((user_id, "\n".join(message_lines)))
    
    return messages


# async def send_notifications():
#     try:
#         now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        
#         connection = MongoDBConnection()
#         db = connection.get_database()
        
#         five_minutes_later = now + timedelta(minutes=5)
        
#         query = {
#             "_deleted": False,
#             "_send_notification_at": {
#                 "$gte": now,
#                 "$lt": five_minutes_later
#             }
#         }
        
#         records = db["RECORDS"].find(query)
#         schemas = db["SCHEMAS"].find()
        
#         print(records)
        
#         connection.close_connection()
        
#         messages = generate_user_messages(records, schemas)
#         tasks = [async_send_message(user_id, msg) for user_id, msg in messages]
#         await asyncio.gather(*tasks)
        
#         logging.info(f"== Send notification job successfully at {now} ==")
        
#     except Exception as e:
#         logging.error(f"== Error happened: {str(e)} ==")
    
def send_notifications(minutes=10):
    try:
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        connection = MongoDBConnection(silent=True)
        db = connection.get_database()
        five_minutes = now + timedelta(minutes=minutes)
        query = {"_deleted": False, "_send_notification_at": { "$gte": now, "$lt": five_minutes}}
        records = list(db["RECORDS"].find(query))
        schemas = list(db["SCHEMAS"].find())

        # collection = defaultdict(list)
        # for record in records:
        #     user_id = record["_user_id"]
        #     clean_data = {k: v for k, v in record.items() if not k.startswith('_')}
        #     if clean_data: collection[user_id].append(clean_data)

        # message = defaultdict(str)
        # for user, records in collection.items():
        #     result = ["🔔 Notification \n"] + [
        #         f"{idx+1}. " + ". ".join([f"{attr.capitalize()}: {value}" for attr, value in record.items()])
        #         for idx, record in enumerate(records)
        #     ]
        #     message[user] = '\n'.join(result)

        messages = generate_user_messages(records, schemas)
        
        db["RECORDS"].update_many(query, {"$set": {"_send_notification_at": None}})
        connection.close_connection()
        return messages
    except Exception as e:
        print(f"Error: {e}")
