import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../lib/supabase'
import { API_BASE } from '../lib/config'
import { fetchFeed, fetchLeaderboard, fetchMarketMood, fetchRecentAlerts, fetchSentimentHistory } from '../api'
import type { MentionItem, TrendSnapshot, MarketMood, AlertItem, SentimentSnapshot } from '../types'

const POLL = 5 * 60 * 1000

export function useFeed(filters?: Parameters<typeof fetchFeed>[0]) {
  const [items, setItems] = useState<MentionItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(() => {
    fetchFeed({ limit: 50, ...filters })
      .then(d => { setItems(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [filters?.source, filters?.sentiment, filters?.coin])

  useEffect(() => {
    setLoading(true)
    refresh()
    const id = setInterval(refresh, POLL)
    const ch = supabase.channel('live-feed')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'mentions' }, (payload) => {
        const item = payload.new as MentionItem
        if (filters?.source && item.source !== filters.source) return
        if (filters?.sentiment && item.sentiment !== filters.sentiment) return
        setItems(prev => [item, ...prev].slice(0, 100))
      }).subscribe()
    return () => { clearInterval(id); supabase.removeChannel(ch) }
  }, [filters?.source, filters?.sentiment, filters?.coin])

  return { items, loading, error }
}

export function useLeaderboard(window: 1|6|24 = 1) {
  const [data, setData] = useState<TrendSnapshot[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const refresh = useCallback(() => {
    fetchLeaderboard(window)
      .then(d => { setData(d); setLastUpdated(new Date()); setLoading(false) })
      .catch(() => setLoading(false))
  }, [window])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, POLL)
    return () => clearInterval(id)
  }, [refresh])

  return { data, loading, lastUpdated, refresh }
}

export function useMarketMood() {
  const [mood, setMood] = useState<MarketMood | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(() => {
    fetchMarketMood().then(d => { setMood(d); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, POLL)
    const ch = supabase.channel('market-mood')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'market_mood' },
        (p) => setMood(p.new as MarketMood)).subscribe()
    return () => { clearInterval(id); supabase.removeChannel(ch) }
  }, [])

  return { mood, loading }
}

export function useAlerts(maxItems = 20) {
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isConnected, setIsConnected] = useState(false)

  const refresh = useCallback(() => {
    fetchRecentAlerts(maxItems).then(setAlerts).catch(console.error)
  }, [maxItems])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, POLL)
    const ch = supabase.channel('alert-stream')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'alert_stream' }, (p) => {
        setAlerts(prev => [p.new as AlertItem, ...prev].slice(0, maxItems))
        setUnreadCount(n => n + 1)
      }).subscribe(s => setIsConnected(s === 'SUBSCRIBED'))
    return () => { clearInterval(id); supabase.removeChannel(ch) }
  }, [maxItems])

  return { alerts, unreadCount, isConnected, markAllRead: () => setUnreadCount(0) }
}

export function useConnectionStatus() {
  const [online, setOnline] = useState(true)

  useEffect(() => {
    const check = async () => {
      try {
        await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) })
        setOnline(true)
      } catch { setOnline(false) }
    }
    check()
    const id = setInterval(check, 30_000)
    return () => clearInterval(id)
  }, [])

  return online
}

export function useSentimentHistory(coin: string, hours = 24) {
  const [data, setData] = useState<SentimentSnapshot[]>([])
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(() => {
    fetchSentimentHistory(coin, hours)
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [coin, hours])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, POLL)
    return () => clearInterval(id)
  }, [coin, hours])

  return { data, loading }
}
