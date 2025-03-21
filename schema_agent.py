from agents import Agent, Runner, trace, TResponseInputItem, RunContextWrapper, function_tool, ModelSettings, FunctionTool
import asyncio
import os
from dotenv import load_dotenv
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, UTC
from dataclasses import dataclass
from pymongo import MongoClient
from pymongo.server_api import ServerApi

from utils.context_funcs import retrieve_all_schemas_in_context
from models.DTOs.context import AssistantContext
from models.DTOs.field import SchemaFieldDto
from models.DTOs.schema import SchemaDto
from models.DTOs.record_base import RecordBaseDto
from models.DTOs.schema_state import SchemaStateDto
from utils.mongodb_handler import MongoDBHandler
from models.DB.schema import Schema
load_dotenv()

openai_api_key = os.environ["OPENAI_API_KEY"]
mongodb_conn = os.environ["MONGODB_CONN"]
db_name = os.environ["MONGODB_DATABASE"]

async def create_schema(wrapper: RunContextWrapper[AssistantContext], args: str) -> str:
    try:
        parsed = SchemaDto.model_validate_json(args)

        now = datetime.now(UTC)
        
        user_id = wrapper.context.user_id
        
        schema_state = SchemaStateDto(schema=parsed, records=[])
        
        wrapper.context.schema_state_list.append(schema_state)
        
        db = MongoDBHandler(mongodb_conn, db_name)
        
        db_schema_value = {
            "user_id": user_id,
            "name": parsed.name,
            "display_name": parsed.display_name,
            "description": parsed.description,
            "fields": [
                {
                    "name": field.name,
                    "display_name": field.display_name,
                    "description": field.description,
                    "data_type": field.data_type,
                    "created_at": now,
                } for field in parsed.fields
            ],
            "created_at": now,
        }
        
        inserted_id = db.insert_document("SCHEMAS", db_schema_value)
        
        db.close_connection()
        
        if inserted_id is None:
            return "Save to database failed"
        
        return "Save successfully"
    except Exception as e:
        return "Error happened"

schema_json_schema = SchemaDto.model_json_schema()
schema_json_schema["additionalProperties"] = False

create_schema_tool = FunctionTool(
    name="create_schema_tool",
    description="Processes extracted schema data and stores it in context.",
    params_json_schema=schema_json_schema,
    on_invoke_tool=create_schema,
)

create_schema_agent = Agent[AssistantContext](
    name="create_schema_agent",
    model="gpt-4o-mini",
    instructions="""
    You’re a helpful AI that creates structured schemas based on user requests.
    Return a schema with:
    - name: Unique, no spaces/special chars (e.g., 'todolist')
    - display_name: Human-readable (e.g., 'Todo List')
    - description: Purpose of the schema
    - fields: List of {name, display_name, description, data_type} (no nested fields)

    Example for a todo list request:
    {
        "name": "todolist",
        "display_name": "Todo List",
        "description": "Task management for user",
        "fields": [
            {"name": "task_name", "display_name": "Task Name", "description": "Task title", "data_type": "string"},
            {"name": "due_date", "display_name": "Due Date", "description": "Task deadline", "data_type": "datetime"}
        ]
    }

    After generating the schema, serialize it to JSON and pass it to the create_schema_tool.
    Based on the tool’s response, craft a personalized reply (e.g., "Your Todo List schema is updated successfully!").
    If multiple schemas are requested, check context and call create_schema_tool in parallel for new ones only.
    """,
    model_settings=ModelSettings(parallel_tool_calls=True),
    tools=[create_schema_tool]
)

async def update_schema(wrapper: RunContextWrapper[AssistantContext], args: str) -> str:
    try:
        parsed = SchemaDto.model_validate_json(args)
        
        now = datetime.now(UTC)
        
        user_id = wrapper.context.user_id
        
        
        db = MongoDBHandler(mongodb_conn, db_name)
        
        db_schema_value = {
            "user_id": user_id,
            "name": parsed.name,
            "display_name": parsed.display_name,
            "description": parsed.description,
            "fields": [
                {
                    "name": field.name,
                    "display_name": field.display_name,
                    "description": field.description,
                    "data_type": field.data_type,
                    "created_at": now,
                } for field in parsed.fields
            ],
            "created_at": now,
        }
        
        modified_count = db.update_document("SCHEMAS", {"user_id": user_id, "name": db_schema_value["name"]}, db_schema_value)
        
        db.close_connection()
        
        if modified_count <= 0:
            return f"Not found {parsed.display_name} in the db"
            
        return f"Updated {parsed.display_name} successfully"
        
    except Exception as e:
        return f"Error happened when updating {parsed.display_name}"

update_schema_tool = FunctionTool(
    name="update_schema_tool",
    description="Processes extracted schema data and pass it to update_schema tool to handle update the schema in the context",
    params_json_schema=schema_json_schema,
    on_invoke_tool=update_schema,
)

update_schema_agent = Agent[AssistantContext](
    name="update_schema_agent",
    model="gpt-4o-mini",
    instructions="""You are a helpful structured AI to update schemas based on user requests. Follow these steps with high priority:

1. Retrieve the target schema from the context (call `retrieve_all_schemas_in_context` if no schema data exists).
2. Apply all requested changes from the user to the target schema.
3. Present the current schema structure and the proposed new structure to the user in a clear format (e.g., "Here’s the current schema: ... Here’s the proposed schema: ... Do you confirm these changes?").
4. WAIT for the user to confirm changes before proceeding. Do NOT call `update_schema_tool` until the user confirmation."
   - If the user denined, ask for further instructions or adjustments.
   - If the user doesn’t respond, do nothing until they do.

After receiving user agreement:
- Serialize the updated schema to JSON with:
  - name: Unique, no spaces/special chars (e.g., 'todolist')
  - display_name: Human-readable (e.g., 'Todo List')
  - description: Purpose of the schema
  - fields: List of {name, display_name, description, data_type} (no nested fields)
- Call `update_schema_tool` ONCE per schema.
- Based on the tool’s response, reply with the final structure (e.g., "Your Todo List schema is ready! Here’s the final structure: ...").

Rules:
1. Do NOT change the schema’s name—it identifies the schema.
2. For a single schema, apply all changes in one step before calling `update_schema_tool`.
3. For multiple schemas, call `update_schema_tool` in parallel, but only once per schema.""",
    tools=[update_schema_tool, retrieve_all_schemas_in_context],
    model_settings=ModelSettings(parallel_tool_calls=True)
)

@function_tool
async def delete_schema(wrapper: RunContextWrapper[AssistantContext], schema_name: str) -> str:
    try:
        target_schema_state = next(schema_state for schema_state in wrapper.context.schema_state_list if schema_state.schema.name == schema_name)
        if target_schema_state:
            db = MongoDBHandler(mongodb_conn, db_name)
            user_id = wrapper.context.user_id
            
            schema_name = target_schema_state.schema.name
            
            deleted_count = db.delete_document("SCHEMAS", {"user_id": user_id, "name": schema_name})
            
            if deleted_count > 0:
                return f"Deleted {schema_name} schema in the database successfully"
        return f"Not found any schema named {schema_name}"
    except Exception as e:
        return f"Error happened while deleting the {schema_name} schema in the context"

delete_schema_agent = Agent[AssistantContext](
    name="delete_schema_agent",
    model="gpt-4o-mini",
    instructions="""You are helpful AI to delete the schema, you decide a schema name that is targeted to remove
    You have to follow:
    1. If you do not have the schema data from your context yet, please call retrieve_all_schemas_in_context to get all schemas.
    2. You have to inform user, waiting feedbacks and confirm to delete that. You have to notice that it will affect on all records belonging to these schemas
    3. Reflect the user request then decide how many schemas to be deleted
    4. If the request involves multiple schemas, call delete_schema tool with schema name in parallel, but only once per distinct schema
    5. Based on the tool's response, craft a personalized reply.
    """,
    tools=[delete_schema, retrieve_all_schemas_in_context],
    model_settings=ModelSettings(parallel_tool_calls=True)
)

recommend_schema_agent = Agent[AssistantContext](
    name = "recommend_schema_agent",
    model="gpt-4o-mini",
    instructions=""" You are helpful assistant, you are responsible for recommending the most detailed schema fields in case of not existing schema in the context based on user input, just recommend fields you are possible to store and most important, notice that no nested field
    Notice that you recommend the Human-readable fields (display name to be friendly with users)
    DO NOT recommend user_id or something like that
    After recommend fields, suggest that you can help them to create that schema in the memory
    """
)

schema_agent = Agent[AssistantContext](
    name="schema_agent",
    model="gpt-4o-mini",
    instructions=""" 
    You are helpful coordinator, you navigate the user's request to sub agents and be responsible for:
    1. If you haven't have the schema data in your memory yet, call the retrieve_all_schemas_in_context tool to retrieve all user's schema information before do anything else, if you have called it, refer to it to response to user about question about schemas and their fields.
    2. If user wants to get something related to schemas and fields, check them in the context and return it in personal style, you don't return data type of the fields except to user request
    3. If user wants to do anything related to existing schemas and their fields, refer to the schema data from retrieve_all_schemas_in_context tool to decide, if it is existing, response that that schema is existed, and return the structure of target schema and recommend some actions related with that schema
    4. You navigate tasks for exact agents if that schema is not existed in memory:
        - If user wants to create schema, then push the requirement to create_schema_agent
        - If user wants to update existing schema, then call update_schema_agent
        - If user wants to delete existing schema, then navigate to delete_schema_agent
        - If user wants to organize something that is not existing in the context, then coordinate to recommend_schema_agent to recommend task and receive feedback
    5. Have to be confirm from user to do actions: create, delete
    6. Have to refer the context, use it to personalize the response.
    7. If user wants to recorver deleted schemas, you have to refer to chat history then notice that you can not recover that, you only can recreate them, waiting for user confirmation, and hand off them for create_schema_agent
    8. DO NOT return records of schemas to user
    9. DO NOT show anything related to user_id, cause it is used to stored in the system
    
    """,
    handoffs=[create_schema_agent, update_schema_agent, delete_schema_agent, recommend_schema_agent],
    tools=[retrieve_all_schemas_in_context]
)

async def main():
    user_id = "khanh"
    with trace(" 2025-03-15 Schema agent"):
        input_items: list[TResponseInputItem] = []

        db = MongoDBHandler(mongodb_conn, db_name)

        db_schemas = db.find_documents("SCHEMAS", {"user_id": user_id})
        
        db_records = db.find_documents("RECORDS", {"user_id": user_id})
        
        schema_states = [
            SchemaStateDto(
                schema=SchemaDto(
                    name=db_schema["name"], 
                    display_name=db_schema["display_name"], 
                    description = db_schema["description"],
                    fields=[SchemaFieldDto(name = field["name"], display_name=field["display_name"], description = field["description"], data_type=field["data_type"]) for field in db_schema["fields"] ]
                    ), 
                records = [RecordBaseDto(id=record["id"], schema_name=record["schema_name"], data=record["data"], metadata=record["metadata"]) for record in db_records if record["schema_name"] == db_schema["name"]]) 
                for db_schema in db_schemas
            ]
        db.close_connection()
        
        context = AssistantContext(user_id="khanh", schema_state_list=schema_states)        
        
        while True:
            msg = input("Message: ")
            input_items.append({"content": msg, "role": "user"})
            
            
            print("context: ", context)
            
            try:
                res = await Runner.run(schema_agent, input_items, context=context)
                input_items = input_items + [res.to_input_list()[-1]]
                print("Agent response: ", res.final_output)
                
            except Exception as e:
                print(f"Error happened, please come again: {e}")
                # break

if __name__ == "__main__":
    asyncio.run(main())