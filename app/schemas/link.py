from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_code: Optional[str] = None
    expires_in_days: Optional[int] = None

class LinkResponse(BaseModel):
    short_code: str
    original_url: str
    short_url: str
    created_at: datetime
    expires_at: Optional[datetime]
    click_count: int
    class Config:
        from_attributes = True