from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class NewsType(Enum):
    
    telegram = "telegram"
    url = "url"
    rss = "RSS"
    api = "API"
    twitter = "TWITTER"

class NewsData(BaseModel):
    id_url: int
    title: str
    text: str
    type: NewsType
    date: datetime