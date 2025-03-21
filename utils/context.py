from dataclasses import dataclass, field
from typing import List, Literal
from pydantic import Field, BaseModel

# Đối tượng đại diện cho schema của 1 cột
class FieldSchema(BaseModel):
    name: str = Field(description="Unique field name, no spaces or special characters")
    description: str = Field(description="Field description")
    data_type: Literal["string", "int", "float", "bool", "datetime"] = Field(description="Field type (string, int, float, bool, datetime)")
    model_config = {"json_schema_extra": {"additionalProperties": False}}

# Đối tượng đại diện cho schema của 1 bảng/collection
class CollectionSchema(BaseModel):
    name: str = Field(description="Unique schema name, no spaces or special characters")
    display_name: str = Field(description="Human-readable schema name")
    description: str = Field(description="Schema description")
    fields: List[FieldSchema] = Field(description="List of fields in schema")
    model_config = {"json_schema_extra": {"additionalProperties": False}}

# Đối tượng ngữ cảnh của mỗi người dùng
# Người dùng bao gồm id và danh sách các collection đã tạo
@dataclass
class UserContext:
    user_id: str
    schemas: List[CollectionSchema] = field(default_factory=list)

