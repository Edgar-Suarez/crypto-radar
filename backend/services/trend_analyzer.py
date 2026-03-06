from db.database import supabase, save_trend_snapshot, save_spike_events
from datetime import datetime, timedelta
from collections import defaultdict
import math

SPIKE_THRESHOLDS = {"low": 1.5, "medium": 3.0, "high": 6.0, "extreme": 12.0}

def fetch_mentions_window(hours: int) -> list[dict]:
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    result = (
        supabase.table("mentions")
        .select("id, title, source, subreddit, feed_name, sentiment_score, coin_mentions, created_at")
        .gte("created_at", since)
        .execute()
    )
    return result.data or []

def count_mentions_per_topic(mentions: list[dict]) -> dict:
    counts = defaultdict(lambda: {"count": 0, "sentiment_sum": 0.0, "sources": set()})
    for m in mentions:
        for coin in (m.get("coin_mentions") or []):
            counts[coin]["count"] += 1
            counts[coin]["sentiment_sum"] += m.get("sentiment_score") or 0.0
            counts[coin]["sources"].add(m.get("source", "unknown"))
    return dict(counts)

def calculate_velocity(recent: int, baseline: float) -> float:
    if baseline == 0:
        return 2.0 if recent > 0 else 0.0
    return round(math.log1p(recent / baseline) * 2, 3)

def calculate_buzz(mention_count: int, velocity: float, sentiment_avg: float, source_div: int) -> float:
    return round(
        velocity * 0.40 +
        source_div * 0.25 +
        min(mention_count / 10, 5.0) * 0.25 +
        (sentiment_avg + 1) * 0.10,
        4
    )

def build_trend_leaderboard(window_hours: int = 1) -> list[dict]:
    recent   = fetch_mentions_window(window_hours)
    baseline = fetch_mentions_window(24)
    baseline_counts = count_mentions_per_topic(baseline)
    recent_counts   = count_mentions_per_topic(recent)

    leaderboard = []
    for topic, data in recent_counts.items():
        count = data["count"]
        sentiment_avg = data["sentiment_sum"] / count if count > 0 else 0.0
        source_div    = len(data["sources"])
        b_count       = baseline_counts.get(topic, {}).get("count", 0)
        b_norm        = b_count * (window_hours / 24)
        velocity      = calculate_velocity(count, b_norm)
        buzz          = calculate_buzz(count, velocity, sentiment_avg, source_div)
        leaderboard.append({
            "topic":          topic,
            "topic_type":     "coin",
            "window":         f"{window_hours}h",
            "mention_count":  count,
            "sentiment_avg":  round(sentiment_avg, 3),
            "velocity_score": velocity,
            "buzz_score":     buzz,
            "sources":        list(data["sources"]),
            "snapshot_at":    datetime.utcnow().isoformat(),
        })

    leaderboard.sort(key=lambda x: x["buzz_score"], reverse=True)
    return leaderboard[:20]

def detect_spikes(leaderboard: list[dict]) -> list[dict]:
    spikes = []
    for item in leaderboard:
        v = item["velocity_score"]
        severity = None
        if v >= SPIKE_THRESHOLDS["extreme"]:   severity = "extreme"
        elif v >= SPIKE_THRESHOLDS["high"]:    severity = "high"
        elif v >= SPIKE_THRESHOLDS["medium"]:  severity = "medium"
        elif v >= SPIKE_THRESHOLDS["low"]:     severity = "low"
        if severity:
            spikes.append({**item, "severity": severity})
    return spikes

def run_trend_analysis():
    print("📊 Running trend analysis...")
    for window in [1, 6, 24]:
        leaderboard = build_trend_leaderboard(window_hours=window)
        save_trend_snapshot(leaderboard)
        if window == 1:
            spikes = detect_spikes(leaderboard)
            save_spike_events(spikes)
            if spikes:
                from services.alert_dispatcher import sync_dispatch_spikes
                sync_dispatch_spikes(spikes)
    print("✅ Trend analysis done")
