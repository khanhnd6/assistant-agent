from utils.context import BaseSchema
from pydantic import Field
from typing import Literal

class UpdateProfile(BaseSchema):
    name: Literal["user_name", "dob", "region", "styles", "interests", "timezone", "instructions"] = Field(description="Tên của trường trong user'profile muốn update")
    value: str = Field(description="Giá trị muốn cập nhật ở trường đó")