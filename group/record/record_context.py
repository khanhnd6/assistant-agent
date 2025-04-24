from typing import Literal, Optional
from utils.context import BaseSchema
from pydantic import Field

class SchemaNameInput(BaseSchema):
    schema_real_name: str = Field(description="The value of `name` field in related schema (not display_name)")

class DeletedRecordInput(BaseSchema):
    schema_real_name: str = Field(description="The value of `name` field in related schema (not display_name)")
    record_id: str = Field(description="The record ID of data record, that is `_record_id`")

class RecordJob(BaseSchema):
    schema_name: str = Field(description="The value of `name` field in related schema (not display_name)")
    action: Literal["create", "update", "delete", None]
    existed: bool = Field(description="Check if schema existed in user's schema")
    request: str = Field(description="Brief for the test to create/update/delete of only one record")

class DataEntry(BaseSchema):
    schema_name: str = Field(description="Schema's name")
    record_id: Optional[str] = Field(description="Record ID", default_factory=None)
    data: str = Field(description="JSON object of data")
    send_notification_at: str = Field(description="Datetime to send a notification for this record in ISO format", default_factory=None)