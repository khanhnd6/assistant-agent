from typing import Literal
from datetime import datetime

class SchemaField:
    name: str
    display_name: str
    description: str
    data_type: Literal["string", "int", "float", "bool", "datetime"]
    created_at: datetime
    updated_at: datetime