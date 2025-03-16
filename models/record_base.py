from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime
import uuid

class RecordBase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique record identifier")
    data: Dict[str, Any] = Field(default_factory=dict, description="Dynamic key-value pairs for record data")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Record last update time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata (e.g., source, tags)")

    def update(self, data: Dict[str, Any] = None, metadata: Dict[str, Any] = None) -> None:
        """Update record data and/or metadata."""
        if data:
            self.data.update(data)
        if metadata:
            self.metadata.update(metadata)
        self.updated_at = datetime.utcnow()