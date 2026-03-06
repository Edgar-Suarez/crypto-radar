from fastapi import APIRouter, Query
from db.database import get_coin_sentiment, get_sentiment_history_series, get_market_mood
from services.sentiment_engine import detect_reversal, TRACKED_COINS

router = APIRouter()

@router.get("/coin/{symbol}")
async def coin_sentiment(symbol: str, window: int = Query(1)):
    data = get_coin_sentiment(symbol.upper(), window)
    return data or {"error": "No data yet"}

@router.get("/coin/{symbol}/history")
async def coin_history(symbol: str, hours: int = Query(24)):
    return get_sentiment_history_series(symbol.upper(), hours)

@router.get("/market-mood")
async def market_mood():
    data = get_market_mood()
    return data or {"error": "No data yet"}

@router.get("/reversals")
async def reversals():
    return [r for coin in TRACKED_COINS if (r := detect_reversal(coin)) is not None]
