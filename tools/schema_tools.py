from agents import FunctionTool, RunContextWrapper
from utils.context import CollectionSchema, UserContext
from utils.database import MongoDBConnection
import ujson as json

async def create_schema(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed = CollectionSchema.model_validate_json(args)
        user_id = wrapper.context.user_id
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        user_schemas = db["SCHEMAS"]
        
        schema = parsed.model_dump()
        schema["user_id"] = user_id
        
        existing_schema = user_schemas.find_one({"user_id": user_id, "name": schema["name"]})
        if existing_schema:
            if not existing_schema["deleted"]:
                return "Schema is existing now"
            else:
                user_schemas.update_one({"user_id": user_id, "name": schema["name"]}, {"$set": {"deleted": False}})
        else:
            user_schemas.insert_one(schema)
        mongodb_connection.close_connection()
        
        return 'Success'
    except Exception as e:
        return f'Error {str(e)}'
    
async def update_schema(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed = CollectionSchema.model_validate_json(args)
        user_id = wrapper.context.user_id
        schema = parsed.model_dump()
        schema["user_id"] = user_id
        schema["deleted"] = False
        
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        user_schemas = db["SCHEMAS"]
        user_schemas.update_one(
            {"user_id": user_id, "name": parsed.name, "deleted": False}, 
            {"$set": schema}
        )
        mongodb_connection.close_connection()
        
        return 'Success'
    except Exception as e:
        return 'Error'

async def delete_schema(wrapper: RunContextWrapper[UserContext], info: str) -> str:
    try:
        user_id = wrapper.context.user_id
        info = json.loads(info)
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        user_schemas = db["SCHEMAS"]
        user_schemas.update_one({"user_id": user_id, "name": info["name"]}, {"$set": {"deleted": True}})
        
        db = mongodb_connection.db
        user_schemas = db["SCHEMAS"]
        user_schemas.update_one({"user_id": user_id, "name": info["name"]}, {"$set": {"deleted": True}})
        mongodb_connection.close_connection()
        
        return 'Success'
    except Exception as e:
        return 'Error'

create_schema_tool = FunctionTool(
    name="create_schema_tool",
    description="""
        This tool accepts a JSON input representing a schema for a database collection.
        The JSON should follow this format:
        {
            "name": "unique_identifier",  # Unique, no spaces or special characters (e.g., 'todolist')
            "display_name": "Human-readable name",  # e.g., 'Todo List'
            "description": "Purpose of the schema",
            "fields": [
                {"name": "field_name", "display_name": "Human-readable name", "description": "Field purpose", "data_type": "string|integer|datetime|bool"}
            ]
        }
        This tool is only invoked when executing the `create` action for schema management.
    """,
    params_json_schema=CollectionSchema.model_json_schema(),
    on_invoke_tool=create_schema,
)

update_schema_tool = FunctionTool(
    name="update_schema_tool",
    description="""
        This tool accepts a JSON input representing an updated schema for a database collection.
        The JSON should follow this format:
        {
            "name": This value must remain unchanged,
            "display_name": This value must remain unchanged,
            "description": "This value must remain unchanged,
            "fields": [
                {"name": "field_name", "display_name": "Human-readable name", "description": "Field purpose", "data_type": "string|integer|datetime|bool"}
            ]
        }
        Only `fields` should be updated while `name` and `description` remain unchanged
        This tool is only invoked when executing the `update` action for schema management.
    """,
    params_json_schema=CollectionSchema.model_json_schema(),
    on_invoke_tool=update_schema,
)

delete_schema_tool = FunctionTool(
    name="delete_schema_tool",
    description="""
        This tool deletes a schema from the database collection.
        It requires an unique name of that schema which want to delete.
        This tool is only invoked when executing the `delete` action for schema management.
        Deletion must be confirmed by the user before execution.
    """,
    params_json_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The unique name of the schema to be deleted."
            }
        },
        "required": ["name"],
        "additionalProperties": False
    },
    on_invoke_tool=delete_schema,
)