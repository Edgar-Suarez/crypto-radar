from fastapi import APIRouter, Query
from db.database import get_recent_alerts, get_alert_stream

router = APIRouter()

@router.get("/recent")
async def recent_alerts(limit: int = Query(20)):
    return get_recent_alerts(limit)

@router.get("/stream")
async def alert_stream(limit: int = Query(10)):
    return get_alert_stream(limit)
