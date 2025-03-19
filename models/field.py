from pydantic import BaseModel, Field
from typing import Optional, Literal,Any
from datetime import datetime

class SchemaField(BaseModel):
    name: str = Field(description="Unique field name, no spaces or special characters")
    display_name: str = Field(description="Human-readable field name")
    description: str = Field(description="Field description")
    data_type: Literal["string", "int", "float", "bool", "datetime"] = Field(
        description="Field type (string, int, float, bool, datetime)"
    )
    class Config:
        extra = "forbid"