from fastapi import APIRouter, Query
from services.trend_analyzer import build_trend_leaderboard
from db.database import get_spike_events, get_topic_history

router = APIRouter()

@router.get("/leaderboard")
async def get_leaderboard(window: int = Query(1, description="1, 6, or 24")):
    return build_trend_leaderboard(window_hours=window)

@router.get("/history/{topic}")
async def get_history(topic: str):
    return get_topic_history(topic)

@router.get("/spikes")
async def get_spikes(severity: str = Query(None)):
    return get_spike_events(severity)
