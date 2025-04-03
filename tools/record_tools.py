from agents import FunctionTool, RunContextWrapper
from utils.database import MongoDBConnection
from utils.context import UserContext, DataEntry, DeleteRecord, RetrieveData
from utils.date import convert_date, convert_to_local_timezone
import json
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
        
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        user_collection = db['RECORDS']
        
        result = user_collection.insert_one(data)
        mongodb_connection.close_connection() 
        
        return f'Success, record_id: {str(result.inserted_id)}'
    except Exception as e:
        return f'Error {str(e)}'
    
create_records_tool = FunctionTool(
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


# async def retrieve_records(wrapper: RunContextWrapper[UserContext], args: str) -> str:
#     try:
#         parsed_data = FilterRecordSchema.model_validate_json(args)
#         parsed_data = parsed_data.model_dump()
        
#         user_id = wrapper.context.user_id
        
#         pipeline = parsed_data["pipeline"]
#         pipeline = json.loads(pipeline) if pipeline else []
#         schema_name = parsed_data["collection"]
        
#         pipeline = convert_date(pipeline)
                
#         is_set_condition = False
#         additional_condition = {
#             "_user_id": user_id,
#             "_schema_name": schema_name
#         }
        
#         for stage in pipeline:
#             if "$match" in stage:
                
#                 if "_deleted" in stage["$match"]:
#                     deleted = stage["$match"]["_deleted"]
#                     additional_condition["_deleted"] = deleted if isinstance(deleted, bool) else (deleted == 1)
                    
#                 stage["$match"].update(additional_condition)
#                 is_set_condition = True
#                 break
        
#         if not is_set_condition:
#             pipeline.insert(0, {
#                 "$match": {
#                     "_user_id": user_id,
#                     "_schema_name": schema_name
#                 }
#             })
        
#         mongodb_connection = MongoDBConnection()
#         db = mongodb_connection.get_database()
#         user_collection = db['RECORDS']
        
#         results = list(user_collection.aggregate(pipeline))
#         mongodb_connection.close_connection()
        
#         print(pipeline)
        
#         return str(results)
#     except Exception as e:
#         return f"Error in retrieving data - {e}"

# retrieve_records_tool = FunctionTool(
#     name="retrieve_record_tool",
#     description="""
# This tool accepts only data structure like this:
# {
#     "pipeline": "JSON array of object to filterring data",
#     "collection": "The REAL name of the schema, not `display_name`"
# }

# **Note**:
#     - The record data is an object with the structure like this:
#     {
#       "_id": "<system identified variable, do not use it anywhere>"
#       "<field1>": "<value1>",
#       "<datetime field2>": <datetime>,
#       "<field3>": <value3>,
#       "<additional field>": <additional value>, // that not in fields of schema
#       "_user_id": "<user id>",
#       "_record_id": "<record id>",
#       "_schema_name": "<the REAL name of the schema, not `display_name`>",
#       "_deleted": False,
#       "_send_notification_at": <datetime> // datetime or null if the record is no need to send notification to user
#     }
    
#     - Based on data structure like that, this tool's is used to query data from MongoDB, it accepts `pipeline` to retrieve data, aggregation,...
#     - `collection` is REAL schema name, not `display_name`.
#     - Do NOT filter by `_record_id`, `_user_id`, just only by `_schema_name`, fields of schema, `_deleted` (the flag whether it is deleted or not, if True passing 1 else passing 0), `_send_notification_at` (datetime that record will be reminded to user).
#     - Data is an object based on fields of schema, filter by it based on REAL field name and data type
#     - Notice that if field type is datetime, passing value in ISO formatted string.
#     - Avoid to use user-defined fields to select, it can make missing possible data
#     - The properties that start with `_` are hyper-parameters, there is no any schema's field named like them (e.g: For `_delete` property, there is not any field named `delete`, so do NOT passing `delete` in stead of `_delete`)
#     - Do NOT missing `_` with hyper properties.
    
    
# """,
#     params_json_schema=FilterRecordSchema.model_json_schema(),
#     on_invoke_tool=retrieve_records,
#     strict_json_schema=True
# )


async def retrieve_records(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed_data = RetrieveData.model_validate_json(args)
        parsed_data = parsed_data.model_dump()
        
        user_id = wrapper.context.user_id
        
        schema_name = parsed_data["schema_name"]
        
        query = {
            "_user_id": user_id,
            "_schema_name": schema_name
        }
        
        projection = {
            "_id": 0
        }
        
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        collection = db['RECORDS']
        
        records = list(collection.find(query, projection))

        mongodb_connection.close_connection()

        records = convert_to_local_timezone(records)
        
        return str(records)
    except Exception as e:
        return f"Error in retrieving data - {e}"

retrieve_records_tool = FunctionTool(
    name="retrieve_record_tool",
    description="""
This tool will return data of target schema and accepts only data structure like this:
{
    "schema_name": "The REAL name of the schema, not `display_name`"
}
""",
    params_json_schema=RetrieveData.model_json_schema(),
    on_invoke_tool=retrieve_records,
    strict_json_schema=True
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
        
        print(data)
        
        data = convert_date(data)
        
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        collection = db['RECORDS']
        
        result = collection.update_one({ "_record_id": record_id,"_user_id": user_id, "_schema_name": schema_name}, {"$set": data})
        
        mongodb_connection.close_connection() 
        
        if result.modified_count <= 0:
            return "Cannot update, miss matching"
        
        return f'Success, `record_id`: {str(result.upserted_id)}'
    except Exception as e:
        return f"Error happened - {e}"



update_record_tool = FunctionTool(
    name="update_record_tool",
    description="""
        This tool is used to update existing record of data, it takes in a JSON input with structure:
        {
            "schema_name": "the REAL schema's name",
            "record_id": "Record ID is `_record_id`",
            "data": "JSON object of data of schema's fields and other properties if existed",
            "send_notification_at": "Datetime to send a notification for this record in ISO format",
            "deleted": "The flag to indicate whether the data is deleted or not, passing 1 if True, else passing 0"
        }
        Remember that only passing **changed fields**
        
        Notes:
        `_schema_name`: the REAL name of the schema this record belongs to, not `display_name`.

        `_data`: Main changed record data based on schema fields, keys are REAL field name, not `display_name` of the schema

        `send_notification_at`: Optional. If the user wants a reminder, otherwise leave it empty or null.
        
        Reflect carefully to fill the data
    """,
    params_json_schema=DataEntry.model_json_schema(),
    on_invoke_tool=update_record,
    strict_json_schema=True
)