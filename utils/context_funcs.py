from agents import function_tool, RunContextWrapper

from models.context import AssistantContext
from models.schema_state import SchemaState
from typing import List
import json

def simplify_schema_context(schema_state_list: List[SchemaState], indent=2) -> str:
    if schema_state_list:
        context_dict = {
            "schema_state_list": [
                schema_state.model_dump() for schema_state in schema_state_list
            ]
        }
        return json.dumps(context_dict, indent=indent, default=str)
    return "No existed schema data in your memory"


@function_tool
async def retrieve_all_schemas_in_context(wrapper: RunContextWrapper[AssistantContext]) -> str:
    return simplify_schema_context(wrapper.context.schema_state_list)

