from agents import FunctionTool, RunContextWrapper
from utils.database import MongoDBConnection
from utils.context import UserContext, DataEntry, DeleteRecord, RetrieveData
from utils.date import convert_date, convert_to_local_timezone
from utils.data_extensions import remove_first_underscore, remove_empty_values
import ujson as json
import uuid

async def create_records(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed = DataEntry.model_validate_json(args)
        parsed_data = parsed.model_dump()
        
        user_id = wrapper.context.user_id
        
        data = json.loads(parsed_data['data'])
        
        
        data["_user_id"] = user_id
        data["_record_id"] = str(uuid.uuid4()) 
        data["_schema_name"] = parsed_data["schema_name"]
        data["_send_notification_at"] = parsed_data["send_notification_at"]
        data["_deleted"] = False
        
        
        data = convert_date(data)
        
        local_tz=str(wrapper.context.user_profile["timezone"])
        data = convert_to_local_timezone(data, local_tz, False)
        
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        user_collection = db['RECORDS']
        
        result = user_collection.insert_one(data)
        mongodb_connection.close_connection() 
        
        return f'Success, record_id: {str(result.inserted_id)}'
    except Exception as e:
        return f'Error {str(e)}'
    
create_record_tool = FunctionTool(
    name="create_record_tool",
    description="""
        This tool creates a new record in the specified collection. Call this tool once for each different item
        It only accepts data in the following structure:
        {
            "_schema_name": "The real name of the schema, not `display_name`",
            "_data": { 
                // JSON data that follows the fields of the selected schema 
                // fields of schema are required
                // Additional information is allowed, optional
            },
            "_send_notification_at": "<datetime> in ISO formatted string"
        }
        Notes:
        `_schema_name`: the REAL name of the schema this record belongs to, not `display_name`.

        `_data`: Main record data based on schema fields, keys are REAL field name, not `display_name` of the schema

        `_send_notification_at`: Optional. If the user wants a reminder, otherwise leave it empty or null.
        
        Allow to call in parallel with different ones
    """,
    params_json_schema=DataEntry.model_json_schema(),
    on_invoke_tool=create_records,
    strict_json_schema=True
)

async def retrieve_records(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed_data = RetrieveData.model_validate_json(args)
        parsed_data = parsed_data.model_dump()
        
        user_id = wrapper.context.user_id
        
        schema_name = parsed_data["schema_name"]
        
        query = {
            "_user_id": user_id,
            "_schema_name": schema_name,
            "_deleted": False
        }
        
        projection = {
            "_id": 0,
            "_user_id": 0,
            "_deleted": 0
        }
        
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        collection = db['RECORDS']
        
        records = list(collection.find(query, projection))

        mongodb_connection.close_connection()

        records = convert_to_local_timezone(records, local_tz=str(wrapper.context.user_profile["timezone"]))
        
        records = remove_first_underscore(records)
        
        records = remove_empty_values(records)
        
        return str(records) if records else "Not found any data"
    except Exception as e:
        return f"Error in retrieving data - {e}"

retrieve_records_tool = FunctionTool(
    name="retrieve_records_tool",
    description="""
This tool will return data of target schema and accepts only data structure like this:
{
    "schema_name": "The REAL name of the schema, not `display_name`"
}
""",
    params_json_schema=RetrieveData.model_json_schema(),
    on_invoke_tool=retrieve_records
)


async def delete_record(wrapper: RunContextWrapper[UserContext], args: str) -> str: 
    try:
        parsed_obj = DeleteRecord.model_validate_json(args)
        parsed_obj = parsed_obj.model_dump()
        
        user_id = wrapper.context.user_id
        record_id, schema_name = parsed_obj["record_id"], parsed_obj["schema_name"]
        
        context_schemas = wrapper.context.schemas
        
        if schema_name not in [schema["name"] for schema in context_schemas]:
            return f"Not found {schema_name}"
        
        db_connection = MongoDBConnection()
        db = db_connection.get_database()
        collection = db["RECORDS"]
        
        delete_result = collection.update_one({"_record_id": record_id, "_user_id": user_id, "_schema_name": schema_name}, {"$set": {"_deleted": True}})
        db_connection.close_connection()
        
        deleted_rows = delete_result.modified_count
        
        if deleted_rows <= 0:
            return "Not found that row matching with provided `record_id` or `schema_name` based on user"
        
        return "Success"
    except Exception as e:
        return f"Error happen - {str(e)}"

delete_record_tool = FunctionTool(
    name="delete_record_tool",
    description="""
    This tool is called to delete 1 row of data only based on `schema_name` and `record_id`, it accepts a JSON data structure like:
    {
        "record_id": "The record ID of data record, that is `_record_id`",
        "schema_name": "The REAL unique schema's name, not `display_name`"
    }
    """,
    params_json_schema=DeleteRecord.model_json_schema(),
    on_invoke_tool=delete_record,
    strict_json_schema=True
)


async def update_record(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed_obj = DataEntry.model_validate_json(args)
        parsed_obj = parsed_obj.model_dump()

        user_id = wrapper.context.user_id
        
        data = json.loads(parsed_obj['data'])
        
        schema_name = parsed_obj["schema_name"]
        record_id = parsed_obj["record_id"]
        
        data["_user_id"] = user_id
        data["_record_id"] = record_id
        data["_schema_name"] = schema_name
        
        if parsed_obj["send_notification_at"]:
            data["_send_notification_at"] = parsed_obj["send_notification_at"]
        
        if parsed_obj["deleted"]:
            data["_deleted"] = parsed_obj["deleted"] == 1
                
        data = convert_date(data)
        
        local_tz=str(wrapper.context.user_profile["timezone"])
        data = convert_to_local_timezone(data, local_tz, False)
        
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        collection = db['RECORDS']
        
        result = collection.update_one({ "_record_id": record_id, "_user_id": user_id, "_schema_name": schema_name}, {"$set": data})
        
        mongodb_connection.close_connection() 
        
        if result.modified_count <= 0:
            return "No data is modified"
        
        return f'Success'
    except Exception as e:
        return f"Error happened - {e}"



update_record_tool = FunctionTool(
    name="update_record_tool",
    description="""
        This tool is used to update existing record of data, it takes in a JSON input with structure:
        {
            "schema_name": <The REAL schema's name>,
            "record_id": <Record ID>,
            "data": <JSON object of data of schema's fields only>,
            "send_notification_at": <Datetime to reminder/send a notification for this record in ISO format>,
            "deleted": <The flag to indicate whether the data is deleted or not, passing 1 if True, else passing 0>
        }
        Remember that only passing **changed fields**
        
        Notes:
        `schema_name`: required, the REAL name of the schema this record belongs to, not `display_name`.
        
        "record_id": required, refer to `_record_id` or `record_id` of data

        `data`: required, Main changed record data based on schema fields, keys are REAL field name, not `display_name` of the schema

        `send_notification_at`: Optional. If the user wants a reminder, otherwise leave it empty or null.
        
        `deleted`: required, "The flag to indicate whether the data is deleted or not, passing 1 if True, else passing 0"
        
        Reflect carefully to fill the data
        Do NOT store duplicated data.
    """,
    params_json_schema=DataEntry.model_json_schema(),
    on_invoke_tool=update_record,
    strict_json_schema=True
)