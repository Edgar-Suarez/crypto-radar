import { useState, useEffect } from 'react'
// ── Header ─────────────────────────────────────────────────
import { useAlerts }       from '../hooks'
import { TrendingUp, Bell, RefreshCw, ExternalLink } from 'lucide-react'
import { useLeaderboard, useMarketMood, useFeed, useSentimentHistory } from '../hooks'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import type { MentionItem, AlertItem } from '../types'

export function Header({ isOnline }: { isOnline: boolean }) {
  const [lastUpdate, setLastUpdate] = useState<string>("")

  useEffect(() => {
    const update = () => setLastUpdate(new Date().toLocaleTimeString())
    update()
    const id = setInterval(update, 5 * 60 * 1000)
    return () => clearInterval(id)
  }, [])
  const { unreadCount } = useAlerts()
  return (
    <header className="border-b border-gray-800 bg-gray-950 px-5 py-3 flex items-center justify-between sticky top-0 z-50 backdrop-blur">
      <div className="flex items-center gap-3">
        <span className="text-xl font-black tracking-tighter text-emerald-400">📡 CRYPTO RADAR</span>
        <span className="hidden sm:block text-xs text-gray-600 uppercase tracking-widest">Intelligence</span>
      </div>
      <div className="flex items-center gap-3">
        {unreadCount > 0 && (
          <span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full animate-pulse">
            {unreadCount}
          </span>
        )}
        <div className="flex items-center gap-1.5 text-xs">
          <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-red-500'}`} />
          <span className={isOnline ? 'text-emerald-400' : 'text-red-400'}>{isOnline ? 'LIVE' : 'OFFLINE'}</span>
        {lastUpdate && (
          <span className="hidden sm:block text-xs text-gray-600">Actualizado: {lastUpdate}</span>
        )}
        </div>
      </div>
    </header>
  )
}

// ── MarketMoodBar ──────────────────────────────────────────
const MOOD_CFG: Record<string, { label: string; color: string; bg: string }> = {
  extreme_fear:  { label: 'EXTREME FEAR',  color: 'text-red-400',     bg: 'bg-red-950/60' },
  fear:          { label: 'FEAR',          color: 'text-orange-400',  bg: 'bg-orange-950/60' },
  neutral:       { label: 'NEUTRAL',       color: 'text-yellow-400',  bg: 'bg-yellow-950/60' },
  greed:         { label: 'GREED',         color: 'text-lime-400',    bg: 'bg-lime-950/60' },
  extreme_greed: { label: 'EXTREME GREED', color: 'text-emerald-400', bg: 'bg-emerald-950/60' },
}

export function MarketMoodBar() {
  const { mood } = useMarketMood()
  if (!mood || !mood.mood_label) return null
  const cfg = MOOD_CFG[mood.mood_label] ?? MOOD_CFG.neutral
  const pct = mood.fear_greed_index

  return (
    <div className={`${cfg.bg} border-b border-gray-800 px-5 py-2 flex flex-wrap items-center justify-between gap-3 text-xs`}>
      <div className="flex items-center gap-3">
        <span className="text-gray-500 uppercase tracking-widest">Market Mood</span>
        <span className={`font-bold ${cfg.color}`}>{cfg.label}</span>
        <span className={`text-xl font-black ${cfg.color}`}>{pct.toFixed(0)}</span>
        <div className="w-32 h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all duration-700 ${cfg.color.replace('text-','bg-')}`} style={{ width: `${pct}%` }} />
        </div>
      </div>
      <div className="flex gap-4 text-gray-500">
        {mood.top_bullish?.length > 0 && (
          <span>🐂 <span className="text-emerald-400">{mood.top_bullish.join(' · ')}</span></span>
        )}
        {mood.top_bearish?.length > 0 && (
          <span>🐻 <span className="text-red-400">{mood.top_bearish.join(' · ')}</span></span>
        )}
      </div>
    </div>
  )
}

// ── Leaderboard ────────────────────────────────────────────
export function Leaderboard() {
  const [win, setWin] = useState<1|6|24>(1)
  const { data, loading, lastUpdated, refresh } = useLeaderboard(win)

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp size={13} className="text-emerald-400" />
          <span className="text-xs font-bold uppercase tracking-widest">Trending</span>
        </div>
        <div className="flex items-center gap-1.5">
          {([1,6,24] as const).map(w => (
            <button key={w} onClick={() => setWin(w)}
              className={`text-xs px-2 py-0.5 rounded transition-colors ${win === w ? 'bg-emerald-400 text-gray-950 font-bold' : 'text-gray-500 hover:text-gray-300'}`}>
              {w}h
            </button>
          ))}
          <button onClick={refresh} className="text-gray-600 hover:text-gray-400 ml-1"><RefreshCw size={11}/></button>
        </div>
      </div>

      <div className="divide-y divide-gray-800/60">
        {loading
          ? Array.from({length:8}).map((_,i) => (
              <div key={i} className="px-4 py-2.5 flex gap-3 animate-pulse">
                <div className="w-4 h-3 bg-gray-800 rounded"/><div className="flex-1 h-3 bg-gray-800 rounded"/><div className="w-8 h-3 bg-gray-800 rounded"/>
              </div>
            ))
          : data.slice(0,10).map((item,i) => {
              const vc = item.velocity_score > 6 ? 'text-red-400' : item.velocity_score > 3 ? 'text-orange-400' : item.velocity_score > 1.5 ? 'text-yellow-400' : 'text-gray-500'
              return (
                <div key={item.topic} className="px-4 py-2.5 flex items-center gap-3 hover:bg-gray-800/40 transition-colors">
                  <span className="text-xs text-gray-600 w-4 text-right">{i+1}</span>
                  <span className="font-bold text-sm flex-1 text-gray-100">{item.topic}</span>
                  <span className="text-xs text-gray-500">{item.mention_count}</span>
                  <span className={`text-xs font-mono ${vc}`}>{item.velocity_score.toFixed(1)}x</span>
                  <div className="w-10 h-1 bg-gray-800 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-400 rounded-full" style={{ width: `${Math.min(100,(item.buzz_score/10)*100)}%` }}/>
                  </div>
                </div>
              )
            })
        }
      </div>
      {lastUpdated && (
        <div className="px-4 py-1.5 text-xs text-gray-700 border-t border-gray-800">
          Updated {lastUpdated.toLocaleTimeString()}
        </div>
      )}
    </div>
  )
}

// ── LiveFeed ───────────────────────────────────────────────
const SRC_COLORS: Record<string, string> = {
  reddit:     'bg-orange-950 text-orange-400 border-orange-800',
  hackernews: 'bg-amber-950 text-amber-400 border-amber-800',
  rss:        'bg-blue-950 text-blue-400 border-blue-800',
  coingecko:  'bg-emerald-950 text-emerald-400 border-emerald-800',
}
const SENT_DOT: Record<string, string> = {
  positive: 'bg-emerald-400', neutral: 'bg-gray-600', negative: 'bg-red-400',
}
function timeAgo(d: string) {
  const mins = Math.floor((Date.now() - new Date(d).getTime()) / 60_000)
  return mins < 1 ? 'just now' : mins < 60 ? `${mins}m` : mins < 1440 ? `${Math.floor(mins/60)}h` : `${Math.floor(mins/1440)}d`
}

export function LiveFeed({ filters }: { filters?: Parameters<typeof useFeed>[0] }) {
  const { items, loading, error } = useFeed(filters)

  if (error) return (
    <div className="bg-red-950/40 border border-red-900 rounded-lg p-4 text-sm text-red-400">
      Error al cargar feed: {error}
    </div>
  )

  return (
    <div className="space-y-2">
      {loading
        ? Array.from({length:6}).map((_,i) => (
            <div key={i} className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 animate-pulse">
              <div className="flex gap-3">
                <div className="w-2 h-2 rounded-full bg-gray-800 mt-1.5"/>
                <div className="flex-1 space-y-2">
                  <div className="h-3.5 bg-gray-800 rounded w-3/4"/>
                  <div className="flex gap-2"><div className="h-4 w-16 bg-gray-800 rounded"/><div className="h-4 w-10 bg-gray-800 rounded"/></div>
                </div>
              </div>
            </div>
          ))
        : items.map(item => <FeedCard key={item.id} item={item} />)
      }
    </div>
  )
}

function FeedCard({ item }: { item: MentionItem }) {
  const srcClass = SRC_COLORS[item.source] ?? 'bg-gray-800 text-gray-400 border-gray-700'
  return (
    <a href={item.url} target="_blank" rel="noopener noreferrer"
       className="block bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 hover:border-gray-600 hover:bg-gray-800/70 transition-all group">
      <div className="flex items-start gap-3">
        <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${SENT_DOT[item.sentiment] ?? 'bg-gray-600'}`}/>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-200 leading-snug line-clamp-2 group-hover:text-white transition-colors">{item.title}</p>
          <div className="mt-1.5 flex items-center gap-1.5 flex-wrap">
            <span className={`text-xs px-1.5 py-0.5 rounded border ${srcClass}`}>
              {item.subreddit ? `r/${item.subreddit}` : item.feed_name ?? item.source}
            </span>
            {item.coin_mentions?.slice(0,3).map(c => (
              <span key={c} className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-700 font-mono">{c}</span>
            ))}
            <span className="text-xs text-gray-600 ml-auto">{timeAgo(item.created_at)}</span>
            {item.score > 0 && <span className="text-xs text-gray-600">↑{item.score}</span>}
          </div>
        </div>
        <ExternalLink size={11} className="text-gray-700 flex-shrink-0 mt-1 group-hover:text-gray-400 transition-colors"/>
      </div>
    </a>
  )
}

// ── SentimentChart ─────────────────────────────────────────
export function SentimentChart({ coin }: { coin: string }) {
  const { data, loading } = useSentimentHistory(coin, 24)
  const chartData = data.map(h => ({
    time:  new Date(h.snapshot_at).toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' }),
    score: h.weighted_score,
  }))
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <div className="text-xs font-bold uppercase tracking-widest mb-3 text-gray-500">{coin} Sentiment 24h</div>
      {loading
        ? <div className="h-24 bg-gray-800/40 rounded animate-pulse"/>
        : data.length === 0
          ? <div className="h-24 flex items-center justify-center text-xs text-gray-700">Esperando datos...</div>
          : (
            <ResponsiveContainer width="100%" height={90}>
              <LineChart data={chartData}>
                <ReferenceLine y={0} stroke="#374151" strokeDasharray="3 3"/>
                <XAxis dataKey="time" hide/>
                <YAxis domain={[-1,1]} hide/>
                <Tooltip
                  contentStyle={{ background:'#111827', border:'1px solid #374151', borderRadius:6, fontSize:11 }}
                  formatter={(v: number) => [v.toFixed(3), 'Sentiment']}
                />
                <Line type="monotone" dataKey="score" stroke="#34d399" strokeWidth={1.5} dot={false} activeDot={{ r:3, fill:'#34d399' }}/>
              </LineChart>
            </ResponsiveContainer>
          )
      }
    </div>
  )
}

// ── AlertsPanel ────────────────────────────────────────────
const SEV_STYLE: Record<string, string> = {
  low:     'border-blue-800/60 bg-blue-950/20',
  medium:  'border-yellow-800/60 bg-yellow-950/20',
  high:    'border-red-800/60 bg-red-950/20',
  extreme: 'border-purple-700/60 bg-purple-950/20',
}

export function AlertsPanel() {
  const { alerts, unreadCount, isConnected, markAllRead } = useAlerts()
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell size={13} className={isConnected ? 'text-emerald-400' : 'text-gray-600'}/>
          <span className="text-xs font-bold uppercase tracking-widest">Alerts</span>
          {unreadCount > 0 && (
            <span className="bg-red-500 text-white text-xs font-bold px-1.5 rounded-full">{unreadCount}</span>
          )}
        </div>
        {unreadCount > 0 && (
          <button onClick={markAllRead} className="text-xs text-gray-600 hover:text-gray-400 transition-colors">mark read</button>
        )}
      </div>
      <div className="divide-y divide-gray-800/60 max-h-[420px] overflow-y-auto scrollbar-thin">
        {alerts.length === 0
          ? <div className="px-4 py-8 text-center text-xs text-gray-700">Monitoring... no alerts yet</div>
          : alerts.map((a, i) => (
              <div key={i} className={`px-4 py-3 border-l-2 ${SEV_STYLE[a.severity] ?? SEV_STYLE.low}`}>
                <div className="flex items-center justify-between mb-0.5">
                  <span className="text-xs font-bold text-gray-200">{a.topic}</span>
                  <span className="text-xs text-gray-600">{new Date(a.sent_at).toLocaleTimeString()}</span>
                </div>
                <p className="text-xs text-gray-400 leading-relaxed">{a.message}</p>
              </div>
            ))
        }
      </div>
    </div>
  )
}

// ── FilterBar ──────────────────────────────────────────────
type Filters = { source?: string; sentiment?: string; coin?: string }

export function FilterBar({ onChange }: { onChange: (f: Filters) => void }) {
  const [active, setActive] = useState<Filters>({})
  const update = (patch: Partial<Filters>) => {
    const next = { ...active, ...patch }
    if (patch.source    && active.source    === patch.source)    delete next.source
    if (patch.sentiment && active.sentiment === patch.sentiment) delete next.sentiment
    setActive(next)
    onChange(next)
  }
  const Chip = ({ label, activeKey, value }: { label: string; activeKey: keyof Filters; value: string }) => (
    <button onClick={() => update({ [activeKey]: value })}
      className={`text-xs px-3 py-1 rounded-full border transition-all ${
        active[activeKey] === value
          ? 'bg-emerald-400 text-gray-950 border-emerald-400 font-bold'
          : 'bg-transparent text-gray-500 border-gray-700 hover:border-gray-500 hover:text-gray-300'
      }`}>
      {label}
    </button>
  )
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <Chip label="Reddit"  activeKey="source" value="reddit"/>
      <Chip label="HN"      activeKey="source" value="hackernews"/>
      <Chip label="RSS"     activeKey="source" value="rss"/>
      <div className="w-px h-4 bg-gray-800"/>
      <Chip label="📈 Positive" activeKey="sentiment" value="positive"/>
      <Chip label="😐 Neutral"  activeKey="sentiment" value="neutral"/>
      <Chip label="📉 Negative" activeKey="sentiment" value="negative"/>
    </div>
  )
}

// Re-export useState since components above use it
import { useState } from 'react'
