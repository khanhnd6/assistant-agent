from agents import Agent, Runner, trace, TResponseInputItem, RunContextWrapper, function_tool, ModelSettings, FunctionTool
import asyncio
import os
from dotenv import load_dotenv
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, UTC
from dataclasses import dataclass

from models.context import AssistantContext
from models.field import SchemaField
from models.schema import Schema
from models.record_base import RecordBase
from models.schema_state import SchemaState
load_dotenv()

openai_api_key = os.environ["OPENAI_API_KEY"]

def simplify_schema_context(schema_state_list: List[SchemaState]) -> str:
    schemas = [schemaState.schema for schemaState in schema_state_list]
    schema_format = """
-   Schema: {schema_name}
    Display Name: {schema_display_name}
    Description: {schema_description}
    Fields: {schema_fields}
     """
    field_format = """
        -   Field: {field_name}
            Display Name: {field_display_name}
            Description: {field_description}
            Data type: {data_type}
    """
     
    if schemas:
        output = ""
        for schema in schemas:
            fields_str=""
            for field in schema.fields:
                fields_str += field_format.format(field_name=field.name, field_display_name=field.display_name, field_description=field.description,data_type=field.data_type)
            schema_info = schema_format.format(
                schema_name=schema.name, 
                schema_display_name=schema.display_name, 
                schema_description=schema.description, 
                schema_fields=fields_str)
            output += schema_info + "\n"
        return output
    return "No existed schema data in your memory"

@function_tool
async def retrieve_all_schemas_in_context(wrapper: RunContextWrapper[AssistantContext]) -> str:
    return simplify_schema_context(wrapper.context.schema_state_list)

async def create_schema(wrapper: RunContextWrapper[AssistantContext], args: str) -> str:
    try:
        parsed = Schema.model_validate_json(args)

        now = datetime.now(UTC)
        
        schema_state = SchemaState(schema=parsed, records=[],created_at=now)
        
        wrapper.context.schema_state_list.append(schema_state)
        return "Save successfully"
    except Exception as e:
        return "Error happened"

schema_json_schema = Schema.model_json_schema()
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
        parsed = Schema.model_validate_json(args)

        now = datetime.now(UTC)
        
        print(parsed)
        
        isUpdated = False
        
        for schema_state in wrapper.context.schema_state_list:
            if(schema_state.schema.name == parsed.name):
                schema_state.schema = parsed
                isUpdated = True
                break
        if isUpdated:
            return f"Updated {parsed.display_name} successfully"
        return f"Not found {parsed.display_name} in the context"
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
            wrapper.context.schema_state_list.remove(target_schema_state)
            return f"Deleted {schema_name} schema in the context successfully"
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
    Notice that you recommend the Human-readable fields
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
    """,
    handoffs=[create_schema_agent, update_schema_agent, delete_schema_agent, recommend_schema_agent],
    tools=[retrieve_all_schemas_in_context]
)

async def main():
    input_items: list[TResponseInputItem] = []
    with trace(" 2025-03-15 Schema agent"):
        schemas = [
            SchemaState(
                schema=Schema(
                    name='todolist', 
                    display_name='Todo List', 
                    description='Task management for users', 
                    fields=[
                        SchemaField(name='task_title', display_name='Task Title', description='Brief title for the task', data_type='string'), 
                        SchemaField(name='description', display_name='Description', description='Detailed description of the task', data_type='string'), 
                        SchemaField(name='due_date', display_name='Due Date', description='Date by which the task should be completed', data_type='datetime'), 
                        SchemaField(name='priority', display_name='Priority', description='Priority level (low, medium, high)', data_type='string'), 
                        SchemaField(name='status', display_name='Status', description='Current status of the task (pending, completed)', data_type='string'), 
                        SchemaField(name='created_date', display_name='Created Date', description='Date when the task was created', data_type='datetime'), 
                        SchemaField(name='assigned_to', display_name='Assigned To', description='Person responsible for the task', data_type='string')
                        ]
                    ), 
                records=[], 
                created_at=datetime(2025, 3, 14))
            ]
        
        initial_context = AssistantContext(schema_state_list=schemas)        
        
        while True:
            msg = input("Message: ")
            input_items.append({"content": msg, "role": "user"})
            
            print("context: ", initial_context)

            try:
                res = await Runner.run(schema_agent, input_items, context=initial_context)
                input_items = res.to_input_list()
                print("Agent response: ", res.final_output)
                
            except Exception as e:
                print(f"Error happened, please come again: {e}")
                # break

if __name__ == "__main__":
    asyncio.run(main())