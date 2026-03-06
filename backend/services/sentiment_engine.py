from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from db.database import (supabase, save_sentiment_history, save_market_mood,
                          get_coin_sentiment, get_sentiment_history_series)
from datetime import datetime, timedelta

analyzer = SentimentIntensityAnalyzer()

TRACKED_COINS = ["BTC","ETH","SOL","ADA","DOT","AVAX","MATIC","LINK","XRP","DOGE","ARB","OP"]

SOURCE_WEIGHTS = {
    "hackernews": 1.5, "reddit": 1.0, "coingecko": 0.8,
}
SUBREDDIT_WEIGHTS = {
    "CryptoCurrency": 1.2, "investing": 1.3, "venturecapital": 1.4,
    "startups": 1.2, "CryptoMoonShots": 0.7, "SatoshiStreetBets": 0.6,
}
RSS_WEIGHTS = {
    "coindesk": 1.4, "decrypt": 1.3, "cointelegraph": 1.2, "techcrunch": 1.3,
}
CRYPTO_BOOSTERS = {
    "moon": 1.5, "mooning": 1.5, "bullish": 1.8, "bull run": 1.8,
    "breakout": 1.3, "gem": 1.4, "undervalued": 1.3, "adoption": 1.3,
    "rug": -2.0, "rugpull": -2.0, "scam": -2.0, "ponzi": -2.0,
    "bearish": -1.8, "dump": -1.5, "crash": -1.8, "rekt": -1.5,
    "hack": -1.8, "exploit": -1.5, "lawsuit": -1.2,
}

def get_weight(mention: dict) -> float:
    source = mention.get("source", "reddit")
    if source == "reddit":
        return SUBREDDIT_WEIGHTS.get(mention.get("subreddit", ""), 1.0)
    if source == "rss":
        return RSS_WEIGHTS.get(mention.get("feed_name", ""), 1.0)
    return SOURCE_WEIGHTS.get(source, 1.0)

def enhanced_sentiment(text: str) -> dict:
    text_lower = text.lower()
    base = analyzer.polarity_scores(text)["compound"]
    adj = sum(w * 0.05 for t, w in CRYPTO_BOOSTERS.items() if t in text_lower)
    adj = max(-0.3, min(0.3, adj))
    score = max(-1.0, min(1.0, base + adj))
    label = "positive" if score >= 0.05 else ("negative" if score <= -0.05 else "neutral")
    return {"score": round(score, 4), "label": label}

def aggregate_coin_sentiment(mentions: list[dict], coin: str) -> dict | None:
    relevant = [m for m in mentions if coin in (m.get("coin_mentions") or [])]
    if not relevant:
        return None
    total_w, weighted_sum = 0.0, 0.0
    pos = neg = neu = 0
    for m in relevant:
        s = enhanced_sentiment(f"{m.get('title','')} {m.get('body','')}")
        w = get_weight(m)
        weighted_sum += s["score"] * w
        total_w += w
        if s["label"] == "positive": pos += 1
        elif s["label"] == "negative": neg += 1
        else: neu += 1
    avg    = sum(m.get("sentiment_score", 0) for m in relevant) / len(relevant)
    wscore = weighted_sum / total_w if total_w > 0 else 0.0
    mood   = ("bullish" if wscore > 0.2 and pos > neg
              else "bearish" if wscore < -0.2 and neg > pos
              else "uncertain")
    return {
        "coin": coin, "avg_score": round(avg, 4), "weighted_score": round(wscore, 4),
        "positive_count": pos, "neutral_count": neu, "negative_count": neg,
        "total_mentions": len(relevant), "dominant_mood": mood,
    }

def calculate_fear_greed(mentions: list[dict]) -> dict:
    if not mentions:
        return {"index": 50.0, "label": "neutral"}
    scores = [enhanced_sentiment(f"{m.get('title','')} {m.get('body','')}") ["score"] * get_weight(m)
              for m in mentions]
    avg   = sum(scores) / len(scores)
    index = round(max(0, min(100, (avg + 1) * 50)), 1)
    label = ("extreme_fear" if index <= 20 else "fear" if index <= 40
             else "neutral" if index <= 60 else "greed" if index <= 80
             else "extreme_greed")
    return {"index": index, "label": label}

def detect_reversal(coin: str, lookback: int = 6) -> dict | None:
    result = (
        supabase.table("sentiment_history")
        .select("weighted_score, snapshot_at")
        .eq("coin", coin).eq("window", "1h")
        .order("snapshot_at", desc=True).limit(lookback).execute()
    )
    history = result.data
    if len(history) < 3:
        return None
    mid         = len(history) // 2
    recent_avg  = sum(h["weighted_score"] for h in history[:mid]) / mid
    older_avg   = sum(h["weighted_score"] for h in history[mid:]) / (len(history) - mid)
    delta       = recent_avg - older_avg
    if abs(delta) < 0.25:
        return None
    return {
        "coin":        coin,
        "direction":   "turning_positive" if delta > 0 else "turning_negative",
        "delta":       round(delta, 4),
        "recent_avg":  round(recent_avg, 4),
        "older_avg":   round(older_avg, 4),
        "detected_at": datetime.utcnow().isoformat(),
    }

def run_sentiment_cycle(window_hours: int = 1):
    from services.trend_analyzer import fetch_mentions_window
    mentions = fetch_mentions_window(window_hours)
    if not mentions:
        return
    snapshots = []
    for coin in TRACKED_COINS:
        agg = aggregate_coin_sentiment(mentions, coin)
        if agg:
            snapshots.append({**agg, "window": f"{window_hours}h",
                              "snapshot_at": datetime.utcnow().isoformat()})
    if snapshots:
        save_sentiment_history(snapshots)
    fg      = calculate_fear_greed(mentions)
    bullish = sorted(snapshots, key=lambda x: x["weighted_score"], reverse=True)
    bearish = sorted(snapshots, key=lambda x: x["weighted_score"])
    save_market_mood({
        "fear_greed_index": fg["index"], "mood_label": fg["label"],
        "top_bullish": [s["coin"] for s in bullish[:3]],
        "top_bearish": [s["coin"] for s in bearish[:3]],
    })
    print(f"✅ Sentiment cycle — F&G: {fg['index']} ({fg['label']})")
