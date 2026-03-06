import { useState } from 'react'
import { Header }        from './components/Header'
import { MarketMoodBar } from './components/MarketMoodBar'
import { Leaderboard }   from './components/Leaderboard'
import { LiveFeed }      from './components/LiveFeed'
import { SentimentChart} from './components/SentimentChart'
import { AlertsPanel }   from './components/AlertsPanel'
import { FilterBar }     from './components/FilterBar'
import { useConnectionStatus } from './hooks'

export default function App() {
  const [filters, setFilters] = useState<{ source?: string; sentiment?: string; coin?: string }>({})
  const isOnline = useConnectionStatus()

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-mono">
      <Header isOnline={isOnline} />
      <MarketMoodBar />

      <main className="max-w-screen-2xl mx-auto px-4 py-5 grid grid-cols-12 gap-4">
        {/* Columna izquierda */}
        <aside className="col-span-12 lg:col-span-3 space-y-4">
          <Leaderboard />
          <SentimentChart coin="BTC" />
        </aside>

        {/* Centro — feed */}
        <section className="col-span-12 lg:col-span-6 space-y-3">
          <FilterBar onChange={setFilters} />
          <LiveFeed filters={filters} />
        </section>

        {/* Columna derecha — alertas */}
        <aside className="col-span-12 lg:col-span-3 space-y-4">
          <AlertsPanel />
        </aside>
      </main>
    </div>
  )
}
