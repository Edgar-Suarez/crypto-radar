-- ============================================================
-- CRYPTO RADAR — Schema completo
-- Ejecutar en: Supabase Dashboard → SQL Editor → New query
-- ============================================================

-- Mentions
CREATE TABLE IF NOT EXISTS mentions (
    id              TEXT PRIMARY KEY,
    source          TEXT NOT NULL,
    subreddit       TEXT,
    feed_name       TEXT,
    title           TEXT NOT NULL,
    body            TEXT,
    url             TEXT NOT NULL,
    score           INTEGER DEFAULT 0,
    num_comments    INTEGER DEFAULT 0,
    sentiment       TEXT DEFAULT 'neutral',
    sentiment_score FLOAT DEFAULT 0.0,
    coin_mentions   TEXT[] DEFAULT '{}',
    fetched_at      TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mentions_source   ON mentions(source);
CREATE INDEX IF NOT EXISTS idx_mentions_created  ON mentions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_mentions_sentiment ON mentions(sentiment);

-- Trending coins
CREATE TABLE IF NOT EXISTS trending_coins (
    id               TEXT PRIMARY KEY,
    symbol           TEXT NOT NULL,
    name             TEXT NOT NULL,
    market_cap_rank  INTEGER,
    thumb_url        TEXT,
    mention_count    INTEGER DEFAULT 0,
    sentiment_score  FLOAT DEFAULT 0.0,
    price_usd        FLOAT,
    price_change_24h FLOAT,
    fetched_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Fetch logs
CREATE TABLE IF NOT EXISTS fetch_logs (
    id          BIGSERIAL PRIMARY KEY,
    source      TEXT NOT NULL,
    items_count INTEGER DEFAULT 0,
    success     BOOLEAN DEFAULT TRUE,
    error_msg   TEXT,
    duration_ms INTEGER,
    fetched_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Trend snapshots
CREATE TABLE IF NOT EXISTS trend_snapshots (
    id              BIGSERIAL PRIMARY KEY,
    window          TEXT NOT NULL,
    topic           TEXT NOT NULL,
    topic_type      TEXT NOT NULL,
    mention_count   INTEGER DEFAULT 0,
    sentiment_avg   FLOAT DEFAULT 0.0,
    velocity_score  FLOAT DEFAULT 0.0,
    buzz_score      FLOAT DEFAULT 0.0,
    sources         TEXT[] DEFAULT '{}',
    snapshot_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_snapshots_topic ON trend_snapshots(topic);
CREATE INDEX IF NOT EXISTS idx_snapshots_buzz  ON trend_snapshots(buzz_score DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_time  ON trend_snapshots(snapshot_at DESC);

-- Spike events
CREATE TABLE IF NOT EXISTS spike_events (
    id           BIGSERIAL PRIMARY KEY,
    topic        TEXT NOT NULL,
    topic_type   TEXT NOT NULL,
    mentions_1h  INTEGER,
    mentions_prev INTEGER,
    growth_pct   FLOAT,
    severity     TEXT,
    detected_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Sentiment history
CREATE TABLE IF NOT EXISTS sentiment_history (
    id              BIGSERIAL PRIMARY KEY,
    coin            TEXT NOT NULL,
    window          TEXT NOT NULL,
    avg_score       FLOAT NOT NULL,
    weighted_score  FLOAT NOT NULL,
    positive_count  INTEGER DEFAULT 0,
    neutral_count   INTEGER DEFAULT 0,
    negative_count  INTEGER DEFAULT 0,
    total_mentions  INTEGER DEFAULT 0,
    dominant_mood   TEXT,
    snapshot_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sentiment_coin ON sentiment_history(coin);
CREATE INDEX IF NOT EXISTS idx_sentiment_time ON sentiment_history(snapshot_at DESC);

-- Market mood (Fear & Greed)
CREATE TABLE IF NOT EXISTS market_mood (
    id               BIGSERIAL PRIMARY KEY,
    fear_greed_index FLOAT,
    mood_label       TEXT,
    top_bullish      TEXT[],
    top_bearish      TEXT[],
    snapshot_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Alert stream (browser push via Realtime)
CREATE TABLE IF NOT EXISTS alert_stream (
    id          BIGSERIAL PRIMARY KEY,
    topic       TEXT NOT NULL,
    message     TEXT NOT NULL,
    severity    TEXT DEFAULT 'medium',
    data        JSONB DEFAULT '{}',
    sent_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Alert log (cooldown tracking)
CREATE TABLE IF NOT EXISTS alert_log (
    id       BIGSERIAL PRIMARY KEY,
    topic    TEXT NOT NULL,
    message  TEXT NOT NULL,
    channel  TEXT NOT NULL,
    sent_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_alert_log_topic ON alert_log(topic, sent_at DESC);

-- ============================================================
-- REALTIME: habilitar en tablas que el frontend escucha
-- ============================================================
ALTER PUBLICATION supabase_realtime ADD TABLE mentions;
ALTER PUBLICATION supabase_realtime ADD TABLE trending_coins;
ALTER PUBLICATION supabase_realtime ADD TABLE market_mood;
ALTER PUBLICATION supabase_realtime ADD TABLE alert_stream;

-- ============================================================
-- ROW LEVEL SECURITY: lectura pública, escritura solo backend
-- ============================================================
ALTER TABLE mentions         ENABLE ROW LEVEL SECURITY;
ALTER TABLE trending_coins   ENABLE ROW LEVEL SECURITY;
ALTER TABLE trend_snapshots  ENABLE ROW LEVEL SECURITY;
ALTER TABLE sentiment_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_mood      ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_stream     ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public read mentions"          ON mentions          FOR SELECT USING (true);
CREATE POLICY "public read trending_coins"    ON trending_coins    FOR SELECT USING (true);
CREATE POLICY "public read trend_snapshots"   ON trend_snapshots   FOR SELECT USING (true);
CREATE POLICY "public read sentiment_history" ON sentiment_history FOR SELECT USING (true);
CREATE POLICY "public read market_mood"       ON market_mood       FOR SELECT USING (true);
CREATE POLICY "public read alert_stream"      ON alert_stream      FOR SELECT USING (true);
