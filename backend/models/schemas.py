from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal

class MentionItem(BaseModel):
    id: str
    source: str
    subreddit: Optional[str] = None
    feed_name: Optional[str] = None
    title: str
    body: Optional[str] = None
    url: str
    score: int = 0
    num_comments: int = 0
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    coin_mentions: list[str] = []
    created_at: str

class TrendSnapshot(BaseModel):
    topic: str
    topic_type: str
    window: str
    mention_count: int
    sentiment_avg: float
    velocity_score: float
    buzz_score: float
    sources: list[str]
    snapshot_at: str
