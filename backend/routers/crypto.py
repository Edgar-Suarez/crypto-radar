from fastapi import APIRouter, Query
from db.database import get_mentions, get_trending_coins
from typing import Optional

router = APIRouter()

@router.get("/feed")
async def get_feed(
    source:    Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    coin:      Optional[str] = Query(None),
    limit:     int           = Query(50, le=200),
    offset:    int           = Query(0),
):
    return get_mentions(source, sentiment, coin, limit, offset)

@router.get("/trending")
async def get_trending(limit: int = Query(10, le=50)):
    return get_trending_coins(limit)
