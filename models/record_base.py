from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class RecordBase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique record identifier")
    schema_name: str = Field(description="name of the schema this record belongs to")
    data: Dict[str, Any] = Field(default_factory=dict, description="Dynamic key-value pairs for record data")
    created_at: Optional[datetime] = Field(default=None, description="Record creation time")
    updated_at: Optional[datetime] = Field(default=None, description="Record last update time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata (e.g., source, tags)")
