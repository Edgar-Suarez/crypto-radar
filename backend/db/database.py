import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
    return create_client(url, key)

supabase: Client = get_supabase()

# ── Mentions ───────────────────────────────────────────────

MENTION_DEFAULTS = {
    "id": "", "source": "", "subreddit": None, "feed_name": None,
    "title": "", "body": None, "url": "", "score": 0, "num_comments": 0,
    "sentiment": "neutral", "sentiment_score": 0.0,
    "coin_mentions": [], "created_at": datetime.utcnow().isoformat()
}

def normalize_mention(item: dict) -> dict:
    """Ensure every item has exactly the same keys as the DB schema."""
    normalized = {}
    for key, default in MENTION_DEFAULTS.items():
        normalized[key] = item.get(key, default)
    return normalized

def upsert_mentions(items: list[dict]) -> int:
    if not items:
        return 0
    try:
        normalized = [normalize_mention(i) for i in items]
        result = supabase.table("mentions").upsert(normalized, on_conflict="id").execute()
        return len(result.data)
    except Exception as e:
        print(f"DB upsert_mentions error: {e}")
        return 0

def get_mentions(source=None, sentiment=None, coin=None, limit=50, offset=0) -> list[dict]:
    query = supabase.table("mentions").select("*")
    if source:    query = query.eq("source", source)
    if sentiment: query = query.eq("sentiment", sentiment)
    if coin:      query = query.contains("coin_mentions", [coin])
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return result.data or []

# ── Trending coins ─────────────────────────────────────────

COIN_DEFAULTS = {
    "id": "", "symbol": "", "name": "", "market_cap_rank": None,
    "thumb_url": None, "mention_count": 0, "sentiment_score": 0.0,
}

def normalize_coin(item: dict) -> dict:
    normalized = {}
    for key, default in COIN_DEFAULTS.items():
        normalized[key] = item.get(key, default)
    return normalized

def upsert_trending_coins(coins: list[dict]) -> int:
    if not coins:
        return 0
    try:
        normalized = [normalize_coin(c) for c in coins]
        result = supabase.table("trending_coins").upsert(normalized, on_conflict="id").execute()
        return len(result.data)
    except Exception as e:
        print(f"DB upsert_trending_coins error: {e}")
        return 0

def get_trending_coins(limit=10) -> list[dict]:
    result = (supabase.table("trending_coins").select("*")
              .order("mention_count", desc=True).limit(limit).execute())
    return result.data or []

# ── Fetch logs ─────────────────────────────────────────────

def log_fetch(source: str, count: int, success: bool, error=None, duration_ms=0):
    try:
        supabase.table("fetch_logs").insert({
            "source": source, "items_count": count, "success": success,
            "error_msg": error, "duration_ms": duration_ms
        }).execute()
    except Exception as e:
        print(f"DB log_fetch error: {e}")

# ── Trend snapshots ────────────────────────────────────────

def save_trend_snapshot(leaderboard: list[dict]):
    if not leaderboard:
        return
    try:
        supabase.table("trend_snapshots").insert(leaderboard).execute()
    except Exception as e:
        print(f"DB save_trend_snapshot error: {e}")

def save_spike_events(spikes: list[dict]):
    if not spikes:
        return
    rows = [{"topic": s["topic"], "topic_type": s["topic_type"],
             "mentions_1h": s["mention_count"],
             "growth_pct": round(s["velocity_score"] * 100, 1),
             "severity": s["severity"]} for s in spikes]
    try:
        supabase.table("spike_events").insert(rows).execute()
    except Exception as e:
        print(f"DB save_spike_events error: {e}")

def get_spike_events(severity=None, limit=50) -> list[dict]:
    query = supabase.table("spike_events").select("*").order("detected_at", desc=True).limit(limit)
    if severity:
        query = query.eq("severity", severity)
    return query.execute().data or []

def get_topic_history(topic: str) -> list[dict]:
    result = (supabase.table("trend_snapshots")
              .select("buzz_score, mention_count, velocity_score, snapshot_at")
              .eq("topic", topic.upper()).eq("window", "1h")
              .order("snapshot_at", desc=True).limit(48).execute())
    return result.data or []

# ── Sentiment ──────────────────────────────────────────────

def save_sentiment_history(snapshots: list[dict]):
    if not snapshots:
        return
    try:
        supabase.table("sentiment_history").insert(snapshots).execute()
    except Exception as e:
        print(f"DB save_sentiment_history error: {e}")

def get_coin_sentiment(symbol: str, window=1) -> dict:
    result = (supabase.table("sentiment_history").select("*")
              .eq("coin", symbol.upper()).eq("window", f"{window}h")
              .order("snapshot_at", desc=True).limit(1).execute())
    return result.data[0] if result.data else {}

def get_sentiment_history_series(symbol: str, hours=24) -> list[dict]:
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    result = (supabase.table("sentiment_history")
              .select("weighted_score, dominant_mood, snapshot_at")
              .eq("coin", symbol.upper()).eq("window", "1h")
              .gte("snapshot_at", since).order("snapshot_at").execute())
    return result.data or []

def save_market_mood(mood: dict):
    try:
        supabase.table("market_mood").insert(mood).execute()
    except Exception as e:
        print(f"DB save_market_mood error: {e}")

def get_market_mood() -> dict:
    result = (supabase.table("market_mood").select("*")
              .order("snapshot_at", desc=True).limit(1).execute())
    return result.data[0] if result.data else {}

# ── Alerts ─────────────────────────────────────────────────

def send_browser_alert(topic: str, message: str, severity: str, data: dict = {}):
    try:
        supabase.table("alert_stream").insert({
            "topic": topic, "message": message,
            "severity": severity, "data": data,
            "sent_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        print(f"DB send_browser_alert error: {e}")

def log_alert(topic: str, message: str, channel: str):
    try:
        supabase.table("alert_log").insert({
            "topic": topic, "message": message, "channel": channel
        }).execute()
    except Exception as e:
        print(f"DB log_alert error: {e}")

def is_on_cooldown(topic: str, cooldown_minutes=60) -> bool:
    since = (datetime.utcnow() - timedelta(minutes=cooldown_minutes)).isoformat()
    result = (supabase.table("alert_log").select("id")
              .eq("topic", topic).gte("sent_at", since).limit(1).execute())
    return len(result.data) > 0

def get_recent_alerts(limit=20) -> list[dict]:
    result = (supabase.table("alert_log").select("*")
              .order("sent_at", desc=True).limit(limit).execute())
    return result.data or []

def get_alert_stream(limit=10) -> list[dict]:
    result = (supabase.table("alert_stream").select("*")
              .order("sent_at", desc=True).limit(limit).execute())
    return result.data or []
