from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any, Union
from datetime import datetime

from .field import SchemaFieldDto


class SchemaDto(BaseModel):
    name: str = Field(description="Unique schema name, no spaces or special characters")
    display_name: str = Field(description="Human-readable schema name")
    description: str = Field(description="Schema description")
    fields: List[SchemaFieldDto] = Field(description="List of fields in schema")
    class Config:
        extra = "forbid"
        allow_mutation = True
