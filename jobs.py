from datetime import datetime, timedelta, timezone
from utils.database import AsyncMongoDBConnection
from collections import defaultdict
from dotenv import load_dotenv
import asyncio
import pytz
import re

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
        message_lines = []
        
        for schema_name, records_list in schemas_data.items():
            if schema_name in schema_map:
                for record in records_list:
                    message_lines.append(f"\n🔔: ")
                    field_map = schema_map[schema_name]["fields"]
                    for key, value in record.items():
                        if key in field_map:
                            display_name = field_map[key]
                            formatted_value = format_value(value)
                            message_lines.append(f" * {display_name}: {formatted_value}")
        
        messages.append((user_id, "\n".join(message_lines)))
    
    return messages

def beautify_field_name(name):
    # Tách theo dấu _ hoặc camelCase rồi viết hoa từng từ
    name = re.sub(r'(?<!^)(?=[A-Z])', '_', name)  # camelCase → snake_case
    parts = name.replace('_', ' ').split()
    return ' '.join(word.capitalize() for word in parts)
    
async def send_notifications(minutes=10):
    try:
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        boundaries = now + timedelta(minutes=minutes)

        connection = AsyncMongoDBConnection()
        await connection.connect()
        db = connection.get_database()

        query = {
            "_deleted": False,
            "_send_notification_at": {"$gte": now, "$lt": boundaries}
        }

        print("📩 Job starting at:", now, "| Searching before:", boundaries)

        records_cursor = db["RECORDS"].find(query)
        schemas_cursor = db["SCHEMAS"].find()
        user_profiles_cursor = db["USER_PROFILES"].find()

        records = await records_cursor.to_list(length=None)
        schemas = await schemas_cursor.to_list(length=None)
        user_profiles_data = await user_profiles_cursor.to_list(length=None)

        schema_map = {
            (str(schema["user_id"]), schema["name"]): schema
            for schema in schemas
        }

        user_profiles = {
            str(profile["user_id"]): profile
            for profile in user_profiles_data
        }

        collection = defaultdict(list)

        for record in records:
            user_id = str(record["_user_id"])
            schema_name = record.get("_schema_name")
            schema = schema_map.get((user_id, schema_name), {})
            result = {}
            if schema:
                field_map = {}
                for field in schema.get("fields", []): field_map[field["name"]] = field["display_name"]
                for key, value in record.items():
                    if key.startswith("_"): continue
                    if key in field_map:
                        result[field_map[key]] = value
                    else:
                        result[beautify_field_name(key)] = value
                display_name = schema.get("display_name")
            else:
                for key, value in record.items():
                    if not key.startswith("_"):
                        result[beautify_field_name(key)] = value
                display_name = "Note"
            collection[user_id].append((display_name, result))

        messages = defaultdict(str)

        for user, user_records in collection.items():
            profile = user_profiles.get(user_id, {})
            timezone_str = profile.get("timezone")
            tz = pytz.timezone(timezone_str) if timezone_str in pytz.all_timezones else None

            message_lines = ["*🔔 Notification 🔔*"]
            for schema_display_name, record in user_records:
                entry_lines = [f"*📌 {schema_display_name if schema_display_name else 'Note'}*"]
                for attr, value in record.items():
                    if isinstance(value, datetime):
                        value = pytz.utc.localize(value) 
                        if tz: value = value.astimezone(tz)
                        value = value.strftime('%Y-%m-%d %H:%M:%S')
                    if isinstance(value, bool):
                        value = "✅" if value else "❌"
                    entry_lines.append(f"• {attr}: {value}")
                message_lines.append("\n".join(entry_lines))
            messages[user] = "\n\n".join(message_lines)

        await db["RECORDS"].update_many(query, {"$set": {"_send_notification_at": None}})
        await connection.close_connection()
        return messages

    except Exception as e:
        print(f"❌ Error in send_notifications: {e}")
        return None
    
# Debug Purpose Only
# async def main():
#     now_utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)
#     send_time = now_utc + timedelta(minutes=1)

#     connection = AsyncMongoDBConnection()
#     await connection.connect()
#     db = connection.get_database()

#     await db["RECORDS"].insert_one({
#         "expenditure_name": "Đi ăn tối",
#         "amount": 150000,
#         "expenditure_date": datetime(2025, 4, 15, 14, 21, tzinfo=timezone.utc),
#         "note": "Thông báo lại sau 4 phút.",
#         "_user_id": 8138225670,
#         "_record_id": "f07b4a66-2619-4565-8476-a3252a037e2a",
#         "_send_notification_at": send_time,
#         "_deleted": False
#     })

#     await db["RECORDS"].insert_one({
#         "expenditure_name": "Đi ăn tối 2",
#         "amount": False,
#         "expenditure_date": datetime(2025, 4, 15, 16, 21, tzinfo=timezone.utc),
#         "note": "Thông báo lại sau 4 phút.",
#         "_user_id": 8138225670,
#         "_send_notification_at": send_time,
#         "_deleted": False
#     })

#     await connection.close_connection()
#     messages = await send_notifications()
#     for uid, msg in messages.items():
#         print(f"📨 Message for {uid}:\n{msg}")

# if __name__ == "__main__":
#     asyncio.run(main())
