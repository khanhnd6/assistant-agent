from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime
from typing import List

from .schema import Schema
from .record_base import RecordBase

class SchemaState(BaseModel):
    schema: Schema
    records: List[RecordBase] = []
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Record last update time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata (e.g., source, tags)")
    class Config: 
        allow_mutation = True