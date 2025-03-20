from dataclasses import dataclass
from typing import Optional, List
from pydantic import BaseModel, Field
from .schema import SchemaDto
from .schema_state import SchemaStateDto

@dataclass
class AssistantContext:
    user_id: str
    schema_state_list: List[SchemaStateDto] = Field(default_factory=list)