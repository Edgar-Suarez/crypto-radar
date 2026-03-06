from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.fetcher import fetch_all_sources
from services.trend_analyzer import run_trend_analysis
from services.sentiment_engine import run_sentiment_cycle

async def _run_fetch():
    await fetch_all_sources()

async def _run_analysis():
    run_trend_analysis()
    run_sentiment_cycle(window_hours=1)

def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")

    scheduler.add_job(_run_fetch,    "interval", minutes=10, id="fetch",   replace_existing=True)
    scheduler.add_job(_run_analysis, "interval", minutes=30, id="analyze", replace_existing=True)

    scheduler.add_job(_run_fetch,    "date", id="fetch_init",   misfire_grace_time=60)
    scheduler.add_job(_run_analysis, "date", id="analyze_init", misfire_grace_time=60)

    scheduler.start()
    print("✅ Scheduler started (fetch/10min, analyze/30min)")
    return scheduler