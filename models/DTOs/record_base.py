from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class RecordBaseDto(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique record identifier")
    schema_name: str = Field(description="name of the schema this record belongs to")
    data: Dict[str, Any] = Field(default_factory=dict, description="Dynamic key-value pairs for record data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata (e.g., source, tags)")
