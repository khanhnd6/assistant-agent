from agents import FunctionTool, RunContextWrapper
from utils.database import MongoDBConnection
from utils.context import UserContext, CreateRecordSchema
from utils.config_record import config_record
from utils.date import convert_date
import json

async def create_records(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed = CreateRecordSchema.model_validate_json(args)
        parsed = parsed.model_dump()
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        user_collection = db[f'{wrapper.context.user_id}_{parsed["collection"]}']
        query = config_record(convert_date(json.loads(parsed["records"])))
        result = user_collection.insert_many(query)
        mongodb_connection.close_connection() 
        return str(result.inserted_ids)
    except Exception as e:
        return f'Error'
    
create_records_tool = FunctionTool(
    name="create_record_tool",
    description="""
        This tool creates new records in the specified collection.
        It takes user data and inserts it into the database.
    """,
    params_json_schema=CreateRecordSchema.model_json_schema(),
    on_invoke_tool=create_records,
)