export type Sentiment = 'positive' | 'neutral' | 'negative'
export type Source    = 'reddit' | 'hackernews' | 'rss' | 'coingecko'
export type Severity  = 'low' | 'medium' | 'high' | 'extreme'
export type Mood      = 'bullish' | 'bearish' | 'uncertain'

export interface MentionItem {
  id: string; source: Source; subreddit?: string; feed_name?: string
  title: string; body?: string; url: string; score: number
  num_comments: number; sentiment: Sentiment; sentiment_score: number
  coin_mentions: string[]; created_at: string
}
export interface TrendSnapshot {
  topic: string; topic_type: string; window: string; mention_count: number
  sentiment_avg: number; velocity_score: number; buzz_score: number
  sources: string[]; snapshot_at: string
}
export interface SpikeEvent {
  id: number; topic: string; mentions_1h: number
  growth_pct: number; severity: Severity; detected_at: string
}
export interface SentimentSnapshot {
  coin: string; avg_score: number; weighted_score: number
  positive_count: number; neutral_count: number; negative_count: number
  total_mentions: number; dominant_mood: Mood; snapshot_at: string
}
export interface MarketMood {
  fear_greed_index: number; mood_label: string
  top_bullish: string[]; top_bearish: string[]; snapshot_at: string
}
export interface AlertItem {
  topic: string; message: string; severity: Severity
  data: Record<string, unknown>; sent_at: string
}
