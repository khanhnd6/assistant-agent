from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field

class PlotArgs(BaseModel):
    records: str = Field(description=""" JSON array of object.Example: 
        [
            { "ticker": "AAPL", "price": 175, "volume": 10000 },
            { "ticker": "GOOGL", "price": 2800, "volume": 5000 },
        ]
    """
    )
    x: Optional[str] = Field(description="Name of the X-axis column")
    y: Optional[str] = Field(description="Name of the Y-axis column")
    chart_type: Literal["line", "bar", "pie"] = Field(description="The type of chart to be drawn")
    model_config = {"json_schema_extra": {"additionalProperties": False}}