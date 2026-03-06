import { apiFetch } from '../lib/fetcher'
import type { MentionItem, TrendSnapshot, SpikeEvent, SentimentSnapshot, MarketMood, AlertItem } from '../types'

export const fetchFeed = (p?: { source?: string; sentiment?: string; coin?: string; limit?: number; offset?: number }) => {
  const qs = new URLSearchParams()
  if (p?.source)    qs.set('source',    p.source)
  if (p?.sentiment) qs.set('sentiment', p.sentiment)
  if (p?.coin)      qs.set('coin',      p.coin)
  if (p?.limit)     qs.set('limit',     String(p.limit))
  if (p?.offset)    qs.set('offset',    String(p.offset))
  return apiFetch<MentionItem[]>(`/api/crypto/feed?${qs}`)
}

export const fetchTrending    = ()                        => apiFetch<TrendSnapshot[]>('/api/crypto/trending')
export const fetchLeaderboard = (w: 1|6|24 = 1)          => apiFetch<TrendSnapshot[]>(`/api/trends/leaderboard?window=${w}`)
export const fetchTopicHistory= (topic: string)           => apiFetch<TrendSnapshot[]>(`/api/trends/history/${topic}`)
export const fetchSpikes      = (sev?: string)            => apiFetch<SpikeEvent[]>(`/api/trends/spikes${sev ? `?severity=${sev}` : ''}`)
export const fetchCoinSentiment = (sym: string, w=1)      => apiFetch<SentimentSnapshot>(`/api/sentiment/coin/${sym}?window=${w}`)
export const fetchSentimentHistory = (sym: string, h=24)  => apiFetch<SentimentSnapshot[]>(`/api/sentiment/coin/${sym}/history?hours=${h}`)
export const fetchMarketMood  = ()                        => apiFetch<MarketMood>('/api/sentiment/market-mood')
export const fetchReversals   = ()                        => apiFetch<object[]>('/api/sentiment/reversals')
export const fetchRecentAlerts= (limit=20)                => apiFetch<AlertItem[]>(`/api/alerts/recent?limit=${limit}`)
