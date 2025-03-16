from dataclasses import dataclass
from typing import Optional, List
from pydantic import BaseModel, Field
from .schema import Schema
from .schema_state import SchemaState

@dataclass
class AssistantContext:
    schema_state_list: List[SchemaState] = Field(default_factory=list)