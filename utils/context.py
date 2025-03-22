from dataclasses import dataclass, field
from typing import List, Literal, Optional
from pydantic import Field, BaseModel
from datetime import date

# Đối tượng đại diện cho yêu cầu đầu vào của hàm vẽ biểu đồ
class PlotSchema(BaseModel):
    data: List[dict] = Field(..., description="Danh sách các dictionary, mỗi dictionary là một hàng dữ liệu.")
    x: Optional[str] = Field(None, description="Cột được chọn làm trục X.")
    y: Optional[str] = Field(None, description="Cột được chọn làm trục Y.")
    chart_type: Literal["line", "scatter", "bar", "hist", "box"] = Field(..., description="Loại biểu đồ cần vẽ.")
    hue: Optional[str] = Field(None, description="Cột dùng để nhóm dữ liệu theo màu sắc.")
    model_config = {"json_schema_extra": {'additionalProperties': False}}

# Đối tượng đại diện cho yêu cầu đầu vào của hàm gửi filter
class FilterRecordSchema(BaseModel):
    pipeline: str = Field(description="JSON array of object")
    collection: str = Field(description="Collection's name of schema")
    model_config = {"json_schema_extra": {"additionalProperties": False}}

# Đối tượng đại diện cho yêu cầu đầu vào của hàm tạo record
class CreateRecordSchema(BaseModel):
    records: str = Field(description="JSON array of object")
    collection: str = Field(description="Collection's name of schema")
    model_config = {"json_schema_extra": {"additionalProperties": False}}

# Đối tượng đại diện cho schema của 1 cột
class FieldSchema(BaseModel):
    name: str = Field(description="Unique field name, no spaces or special characters")
    description: str = Field(description="Field description")
    data_type: Literal["string", "int", "float", "bool", "datetime"] = Field(description="Field type (string, int, float, bool, datetime)")
    model_config = {"json_schema_extra": {"additionalProperties": False}}

# Đối tượng đại diện cho schema của 1 bảng/collection
class CollectionSchema(BaseModel):
    name: str = Field(description="Unique schema name, no spaces or special characters")
    display_name: str = Field(description="Human-readable schema name")
    description: str = Field(description="Schema description")
    fields: List[FieldSchema] = Field(description="List of fields in schema")
    deleted: bool = Field(description="Flag to determine whether this schema is deleted or not", default_factory=False)
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    
class UserProfile(BaseModel):
    user_id: Optional[str] = Field(default=None, description="User Id")
    name: Optional[str] = Field(default=None, description="User name")
    dob: Optional[date] = Field(default=None, description="Date of birth")
    interests: Optional[list[str]] = Field(default_factory=list, description="Interests")
    region: Optional[str] = Field(default=None, description="Current user's region")
    language: Optional[str] = Field(default="English", description="User language")
    model_config = {"json_schema_extra": {"additionalProperties": False}}
    
# Đối tượng ngữ cảnh của mỗi người dùng
# Người dùng bao gồm id và danh sách các collection đã tạo
@dataclass
class UserContext:
    user_id: str
    schemas: List[CollectionSchema] = field(default_factory=list)

