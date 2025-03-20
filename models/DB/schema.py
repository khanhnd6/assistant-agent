from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any, Union
from datetime import datetime

from .field import SchemaField


class Schema:
    user_id: str
    name: str
    display_name: str
    description: str
    fields: List[SchemaField]
    created_at = datetime
    updated_at = datetime
