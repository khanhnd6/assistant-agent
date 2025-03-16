from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any, Union
from datetime import datetime

from .field import SchemaField
from .record_base import RecordBase


class Schema(BaseModel):
    name: str = Field(description="Unique schema name, no spaces or special characters")
    display_name: str = Field(description="Human-readable schema name")
    description: str = Field(description="Schema description")
    fields: List[SchemaField] = Field(description="List of fields in schema")
    class Config:
        extra = "forbid"
        allow_mutation = True
