from agents import RunContextWrapper
from utils.context import UserContext
import copy

def retrieve_user_profile(wrapper: RunContextWrapper[UserContext]) -> str:
    user_data = wrapper.context.user_profile
    dob_str = user_data["dob"] if user_data["dob"] is not None else "Not specified"
    interests_str = ", ".join(user_data["interests"]) if user_data["interests"] else "None listed"
    instructions_str = ", ".join(user_data["instructions"]) if user_data["instructions"] else "None"
    timezone_str = user_data["timezone"] if user_data["timezone"] else "None"
    profile = f"""
        Username: {user_data['user_name']},
        Region: {user_data['region']},
        Dob: {dob_str},
        Interests: {interests_str},
        Instructions: {instructions_str},
        Timezone: {timezone_str}
    """
    return profile

def retrieve_schemas(wrapper: RunContextWrapper[UserContext]) -> str:
    schemas = wrapper.context.schemas
    return [schema['name'] for schema in schemas] if schemas else "Empty"

def retrieve_display_schemas(wrapper: RunContextWrapper[UserContext]) -> str:
    schemas = wrapper.context.schemas
    return [schema['display_name'] for schema in schemas] if schemas else "Empty"

def retrieve_brief_schemas(wrapper: RunContextWrapper[UserContext]) -> str:
    schemas = wrapper.context.schemas
    if not schemas: return "Empty"
    result = []
    for idx, schema in enumerate(schemas, start=1):
        result.append(f"`{idx}) real_name: {schema['name']}, description: {schema['description']}`")
    return "\n".join(result)

def retrieve_struct_schemas(wrapper: RunContextWrapper[UserContext]) -> str:
    schemas = copy.deepcopy(wrapper.context.schemas)
    result = []
    for idx, schema in enumerate(schemas, start=1):
        schema.pop("display_name", None)
        real_name = schema.get("name", None)
        field_names = []
        for field in schema.get("fields", []):
            field.pop("display_name", None)
            field_names.append(field.get("name"))
        line = (
            f"{idx}) "
            f"schema_real_name: {real_name}\n"
            f"- fields: {field_names}\n"
            f"- structures: {schema}"
        )
        result.append(line)
    return '\n'.join(result)