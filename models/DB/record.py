from typing import Dict, Any
from datetime import datetime

class Record:
    id: str
    user_id: str
    schema_name: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
