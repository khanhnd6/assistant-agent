from dataclasses import dataclass, field
from typing import List, Literal, Optional, Dict
from pydantic import Field, BaseModel
from datetime import date

class BaseSchema(BaseModel):
    model_config = {"json_schema_extra": {"additionalProperties": False}}

class PlotRecordsSchema(BaseSchema):
    records: str = Field(description="JSON array of object")
    x: Optional[str] = Field(description="Cột được chọn làm trục X.")
    y: Optional[str] = Field(description="Cột được chọn làm trục Y.")
    chart_type: Literal["line", "scatter", "bar", "hist", "box"] = Field(description="Loại biểu đồ cần vẽ.")
    hue: Optional[str] = Field(description="Cột dùng để nhóm dữ liệu theo màu sắc.")

# Đối tượng đại diện cho yêu cầu đầu vào của hàm gửi filter
class FilterRecordSchema(BaseSchema):
    pipeline: str = Field(description="JSON array of object")
    collection: str = Field(description="Collection's name of schema")

# Đối tượng đại diện cho yêu cầu đầu vào của hàm tạo record
class CreateRecordSchema(BaseSchema):
    records: str = Field(description="JSON array of object")
    collection: str = Field(description="Collection's name of schema")

class DataEntry(BaseSchema):
    schema_name: str = Field(description="Schema's name")
    record_id: Optional[str] = Field(description="Record ID", default_factory=None)
    data: str = Field(description="JSON object of data")
    send_notification_at: str = Field(description="Datetime to send a notification for this record in ISO format", default_factory=None)
    deleted: Optional[int] = Field(description="The flag to indicate whether the data is deleted or not, 0 is False, 1 is True", default_factory=0) # 0 - False/ 1 - True
#    categories = list[str] = Field(description="Data categories")

class RetrieveData(BaseSchema):
    schema_name: str = Field(description="The REAL schema name, unique")

class DeleteRecord(BaseSchema):
    record_id: str = Field(description="The record ID of data record")
    schema_name: str = Field(description="The REAL unique schema's name")


# Đối tượng đại diện cho schema của 1 cột
class FieldSchema(BaseSchema):
    name: str = Field(description="Unique field name, no spaces or special characters")
    display_name: str = Field(description="Human-readable name")
    description: str = Field(description="Field description")
    data_type: Literal["string", "int", "float", "bool", "datetime"] = Field(description="Field type (string, int, float, bool, datetime)")

# Đối tượng đại diện cho schema của 1 bảng/collection
class CollectionSchema(BaseSchema):
    user_id: Optional[str] = Field(description="User Id", default_factory=None)
    name: str = Field(description="Unique schema name, no spaces or special characters")
    display_name: str = Field(description="Human-readable schema name")
    description: str = Field(description="Schema description")
    fields: List[FieldSchema] = Field(description="List of fields in schema")
    deleted: bool = Field(description="Flag to determine whether this schema is deleted or not", default_factory=False)
    
class UserProfile(BaseSchema):
    user_id: Optional[str] = Field(default_factory=None, exclude=True, description="User Id")
    user_name: Optional[str] = Field(default_factory=None, description="User name")
    dob: Optional[str] = Field(default_factory=None, description="Date of birth in ISO formatted string")
    region: Optional[str] = Field(default_factory=None, description="Current user's region")
    styles: Optional[str] = Field(default_factory=None, description="Styles")
    interests: Optional[List[str]] = Field(default_factory=None, description="Interests")
    instructions: Optional[List[str]] = Field(default_factory=None, description="Instructions for personal direction")

class UserProfileOutput(BaseSchema):
    status: Literal["Success", "Error", "Fail"]
    # message: str
    call_again: bool


class RecordCommand(BaseSchema):
    schema_name: str
    action: Literal["create", "update", "delete", None]
    existed: bool
    confirmed: bool
    command: str

class RecordCommands(BaseSchema):
    commands: list[RecordCommand]

    

# Đối tượng ngữ cảnh của mỗi người dùng
# Người dùng bao gồm id và danh sách các collection đã tạo
@dataclass
class UserContext:
    user_id: str
    schemas: List[CollectionSchema] = field(default_factory=list)
    user_profile: UserProfile = field(default=None)

