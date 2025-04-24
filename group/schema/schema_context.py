from typing import List, Literal, Optional
from utils.context import BaseSchema
from pydantic import Field

class FieldSchema(BaseSchema):
    name: str = Field(description="Unique field name, no spaces or special characters")
    display_name: str = Field(description="Human-readable name")
    description: str = Field(description="Field description")
    data_type: Literal["string", "int", "float", "bool", "datetime"] = Field(description="Field type (string, int, float, bool, datetime)")

class CollectionSchema(BaseSchema):
    user_id: Optional[int] = Field(description="User Id", default_factory=None)
    name: str = Field(description="Unique schema name, no spaces or special characters")
    display_name: str = Field(description="Human-readable schema name")
    description: str = Field(description="Schema description")
    fields: List[FieldSchema] = Field(description="List of fields in schema")
    deleted: bool = Field(description="Flag to determine whether this schema is deleted or not", default_factory=False)

class ActionResult(BaseSchema):
    is_success: bool
    message: Optional[str]
    data: Optional[str]