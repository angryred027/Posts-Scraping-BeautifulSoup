from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict
from datetime import datetime

class Post(BaseModel):
    platform: str
    url: HttpUrl
    external_id: str
    title: str
    content: str
    author: str
    published_at: datetime
    engagement: Optional[Dict[str, int]] = None
    summary: Optional[str] = None
    score: Optional[int] = None
    suggested_replies: Optional[str] = None