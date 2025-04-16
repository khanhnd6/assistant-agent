from datetime import datetime, timedelta, timezone
from utils.database import AsyncMongoDBConnection
from collections import defaultdict
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

        print("📩 Job starting at:", now, "| Searching until:", boundaries)

        records_cursor = db["RECORDS"].find(query)
        schemas_cursor = db["SCHEMAS"].find()

        records = await records_cursor.to_list(length=None)
        schemas = await schemas_cursor.to_list(length=None)

        schema_map = {
            (str(schema["user_id"]), schema["name"]): schema
            for schema in schemas
        }

        collection = defaultdict(list)

        for record in records:
            user_id = str(record["_user_id"])
            schema_name = record.get("_schema_name")
            schema = schema_map.get((user_id, schema_name), {})
            field_map = {
                field["name"]: field["display_name"]
                for field in schema.get("fields", [])
            }

            clean_data = {
                field_map.get(k, k): v
                for k, v in record.items()
                if not k.startswith("_") and k in field_map
            }

            if clean_data:
                collection[user_id].append(clean_data)

        messages = defaultdict(str)

        for user, user_records in collection.items():
            result = [
                f"🔔 " + ". ".join([f"{attr.capitalize()}: {value}" for attr, value in record.items()])
                for record in user_records
            ]
            messages[user] = '\n\n'.join(result)

        await db["RECORDS"].update_many(query, {"$set": {"_send_notification_at": None}})
        await connection.close_connection()

        return messages

    except Exception as e:
        print(f"❌ Error in send_notifications: {e}")
        return None