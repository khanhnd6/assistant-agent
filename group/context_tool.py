from agents import RunContextWrapper
from utils.context import UserContext
import copy

def retrieve_user_profile(wrapper: RunContextWrapper[UserContext]) -> str:
    profile = wrapper.context.user_profile
    user_name = profile["user_name"] if profile is not None else "Not specified"
    dob_str = profile["dob"] if profile is not None else "Not specified"
    interests_str = ", ".join(profile["interests"]) if profile else "None listed"
    instructions_str = ", ".join(profile["instructions"]) if profile else "None"
    timezone_str = profile["timezone"] if profile else "None"
    region = profile["region"] if profile else "None"
    profile = f"""
        Username: {user_name},
        Region: {region},
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