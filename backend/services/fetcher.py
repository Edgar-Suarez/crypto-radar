import httpx
import asyncio
import feedparser
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

HEADERS = {"User-Agent": "CryptoRadar/1.0 (research bot)"}

SUBREDDITS = ["CryptoCurrency", "CryptoMoonShots", "startups", "investing", "SatoshiStreetBets"]

RSS_FEEDS = {
    "coindesk":      "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "decrypt":       "https://decrypt.co/feed",
    "cointelegraph": "https://cointelegraph.com/rss",
    "techcrunch":    "https://techcrunch.com/category/startups/feed/",
}

KNOWN_COINS = {
    "BTC": "Bitcoin", "ETH": "Ethereum", "SOL": "Solana",
    "ADA": "Cardano", "DOT": "Polkadot", "AVAX": "Avalanche",
    "MATIC": "Polygon", "LINK": "Chainlink", "XRP": "Ripple",
    "DOGE": "Dogecoin", "SHIB": "Shiba Inu", "ARB": "Arbitrum",
    "OP": "Optimism", "SUI": "Sui", "APT": "Aptos",
    "NEAR": "Near", "ATOM": "Cosmos", "FTM": "Fantom",
}

CRYPTO_BOOSTERS = {
    "moon": 1.5, "mooning": 1.5, "bullish": 1.8, "bull run": 1.8,
    "breakout": 1.3, "accumulate": 1.2, "gem": 1.4, "undervalued": 1.3,
    "partnership": 1.2, "mainnet": 1.1, "launch": 1.1, "adoption": 1.3,
    "rug": -2.0, "rugpull": -2.0, "scam": -2.0, "ponzi": -2.0,
    "bearish": -1.8, "dump": -1.5, "dumping": -1.5, "crash": -1.8,
    "rekt": -1.5, "overvalued": -1.2, "sec": -0.8, "hack": -1.8,
}

_cache = {"mentions": [], "trending": [], "last_updated": None}

# ── Sentiment ──────────────────────────────────────────────

def analyze_sentiment(text: str) -> dict:
    text_lower = text.lower()
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]
    adjustment = 0.0
    for term, weight in CRYPTO_BOOSTERS.items():
        if term in text_lower:
            adjustment += weight * 0.05
    adjustment = max(-0.3, min(0.3, adjustment))
    final = max(-1.0, min(1.0, compound + adjustment))
    label = "positive" if final >= 0.05 else ("negative" if final <= -0.05 else "neutral")
    return {"score": round(final, 3), "label": label}

def extract_coin_mentions(text: str) -> list[str]:
    text_upper = text.upper()
    return [sym for sym, name in KNOWN_COINS.items()
            if sym in text_upper or name.upper() in text_upper]

def enrich(items: list[dict]) -> list[dict]:
    for item in items:
        text = f"{item.get('title', '')} {item.get('body', '')}"
        s = analyze_sentiment(text)
        item["sentiment"] = s["label"]
        item["sentiment_score"] = s["score"]
        item["coin_mentions"] = extract_coin_mentions(text)
    return items

# ── Reddit ─────────────────────────────────────────────────

async def fetch_reddit(subreddit: str, limit: int = 25) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            posts = resp.json()["data"]["children"]
            return [
                {
                    "id": p["data"]["id"],
                    "source": "reddit",
                    "subreddit": subreddit,
                    "title": p["data"]["title"],
                    "body": p["data"].get("selftext", "")[:500],
                    "url": f"https://reddit.com{p['data']['permalink']}",
                    "score": p["data"]["score"],
                    "num_comments": p["data"]["num_comments"],
                    "created_at": datetime.utcfromtimestamp(p["data"]["created_utc"]).isoformat(),
                }
                for p in posts if not p["data"].get("stickied")
            ]
        except Exception as e:
            print(f"Reddit r/{subreddit} error: {e}")
            return []

async def fetch_all_reddit() -> list[dict]:
    results = await asyncio.gather(*[fetch_reddit(s) for s in SUBREDDITS])
    all_posts = [p for sub in results for p in sub]
    return sorted(all_posts, key=lambda x: x["score"], reverse=True)

# ── Hacker News ────────────────────────────────────────────

async def fetch_hn(limit: int = 30) -> list[dict]:
    base = "https://hacker-news.firebaseio.com/v0"
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(f"{base}/topstories.json")
            ids = resp.json()[:limit]
            async def get_story(sid):
                try:
                    r = await client.get(f"{base}/item/{sid}.json")
                    return r.json()
                except:
                    return None
            stories = await asyncio.gather(*[get_story(sid) for sid in ids])
            return [
                {
                    "id": str(s["id"]),
                    "source": "hackernews",
                    "title": s.get("title", ""),
                    "url": s.get("url", f"https://news.ycombinator.com/item?id={s['id']}"),
                    "score": s.get("score", 0),
                    "num_comments": s.get("descendants", 0),
                    "created_at": datetime.utcfromtimestamp(s.get("time", 0)).isoformat(),
                }
                for s in stories if s and s.get("type") == "story"
            ]
        except Exception as e:
            print(f"HN error: {e}")
            return []

# ── RSS ────────────────────────────────────────────────────

async def fetch_rss(name: str, url: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url)
            feed = feedparser.parse(resp.text)
            items = []
            for entry in feed.entries[:15]:
                try:
                    pub = parsedate_to_datetime(entry.get("published", "")).isoformat()
                except:
                    pub = datetime.utcnow().isoformat()
                items.append({
                    "id": entry.get("id", entry.get("link", "")),
                    "source": "rss",
                    "feed_name": name,
                    "title": entry.get("title", ""),
                    "body": entry.get("summary", "")[:400],
                    "url": entry.get("link", ""),
                    "score": 0,
                    "num_comments": 0,
                    "created_at": pub,
                })
            return items
        except Exception as e:
            print(f"RSS {name} error: {e}")
            return []

async def fetch_all_rss() -> list[dict]:
    results = await asyncio.gather(*[fetch_rss(n, u) for n, u in RSS_FEEDS.items()])
    return [item for sub in results for item in sub]

# ── CoinGecko ──────────────────────────────────────────────

async def fetch_coingecko_trending() -> list[dict]:
    url = "https://api.coingecko.com/api/v3/search/trending"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            coins = resp.json().get("coins", [])
            return [
                {
                    "id": c["item"]["id"],
                    "symbol": c["item"]["symbol"].upper(),
                    "name": c["item"]["name"],
                    "market_cap_rank": c["item"].get("market_cap_rank"),
                    "thumb_url": c["item"].get("thumb"),
                    "mention_count": 0,
                    "sentiment_score": 0.0,
                }
                for c in coins
            ]
        except Exception as e:
            print(f"CoinGecko error: {e}")
            return []

# ── Master fetch ───────────────────────────────────────────

async def fetch_all_sources():
    from db.database import upsert_mentions, upsert_trending_coins, log_fetch
    print("🔄 Fetching all sources...")
    start = time.time()

    reddit, hn, rss, coins = await asyncio.gather(
        fetch_all_reddit(),
        fetch_hn(),
        fetch_all_rss(),
        fetch_coingecko_trending(),
    )

    all_items = enrich(reddit + hn + rss)
    all_items.sort(key=lambda x: x.get("score", 0), reverse=True)

    saved = upsert_mentions(all_items)
    upsert_trending_coins(coins)

    duration = int((time.time() - start) * 1000)
    log_fetch("all", saved, True, duration_ms=duration)

    _cache["mentions"] = all_items
    _cache["trending"] = coins
    _cache["last_updated"] = datetime.utcnow().isoformat()
    print(f"✅ Fetched & saved {saved} items in {duration}ms")

def get_cached_data(key: str):
    return _cache.get(key, [])
