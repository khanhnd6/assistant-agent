from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime
from typing import List

from .schema import SchemaDto
from .record_base import RecordBaseDto

class SchemaStateDto(BaseModel):
    schema: SchemaDto
    records: List[RecordBaseDto] = []