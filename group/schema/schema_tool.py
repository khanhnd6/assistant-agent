from agents import FunctionTool, RunContextWrapper, Agent
from group.prompt import STANDALONE_PREFIX_PROMPT
from group.context_tool import retrieve_schemas
from utils.database import MongoDBConnection
from group.schema.schema_context import *
from utils.context import UserContext
import ujson as json

async def dynamic_schema_agent_instruction(wrapper: RunContextWrapper[UserContext], agent: Agent[UserContext]) -> str:
  schemas = wrapper.context.schemas or "Empty"
  instruction = f"""
  {STANDALONE_PREFIX_PROMPT}
  Your role is to manage the user's data schemas: you can create, update, or delete schemas based on user instruction, 
  always acting immediately, **never ask for confirmation or suggestion from user**. Just announce when you have the job done!
  
  1. Create schema:
  - Take a look at previous schemas name: {retrieve_schemas(wrapper)}. Find if there is any relevant schema existed:
    + If there is, ask user to use that existing schema or create a new one
    + If not, prepare the data carefully accroding to `create_schema_tool` input format. All display_name fields must be \
      written in the user’s language (ngôn ngữ của người dùng).

  2. Update schema:
  - Take a look at all user's schema structures: {schemas}. Choose the most relevant schema from list.
  - Prepare the data carefully accroding to `update_schema_tool` input format

  3. Delete schema:
  - Take a look at all schemas name: {retrieve_schemas(wrapper)}. Choose the most relevant schema's name from list.
  - Inform the user that deletion is permanent and not recoverable. Then pass that name to `delete_schema_tool` immediately.

  4. Show schema structure:
  - Explain schemas in a clear, personalized, and friendly way.
  - Never show internal (real) `name` values; use only human-readable `display_name` and `description`.
  """
  return instruction

async def create_schema(wrapper: RunContextWrapper[UserContext], args: str) -> ActionResult:
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
        
        return ActionResult(is_success=True, message=f"Successfully created schema named: {schema['name']}", data=str(schema))
    except Exception as e:
        return ActionResult(is_success=False, message=f"Error: {str(e)}", data=None)
    
async def update_schema(wrapper: RunContextWrapper[UserContext], args: str) -> ActionResult:
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
        return ActionResult(is_success=True, message="", data=str(schema))
    except Exception as e:
        return ActionResult(is_success=False, message=f"Error: {str(e)}", data=None)

async def delete_schema(wrapper: RunContextWrapper[UserContext], info: str) -> ActionResult:
    try:
        user_id = wrapper.context.user_id
        info = json.loads(info)
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        user_schemas = db["SCHEMAS"]
        user_schemas.update_one({"user_id": user_id, "name": info["name"]}, {"$set": {"deleted": True}})
        
        return ActionResult(is_success=True, message="Deleted", data=None)
    except Exception as e:
        return ActionResult(is_success=False, message=f"Error: {str(e)}", data=None)

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
    on_invoke_tool=create_schema
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