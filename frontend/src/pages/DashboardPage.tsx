import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getOverview, getTopVideos } from '../api/dashboard'
import type { DashboardOverview, VideoItem } from '../api/dashboard'
import KpiCard from '../components/KpiCard'
import TopVideosTable from '../components/TopVideosTable'

function KpiSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow p-6 animate-pulse">
      <div className="h-3 bg-gray-200 rounded w-24 mb-3" />
      <div className="h-8 bg-gray-200 rounded w-32" />
    </div>
  )
}

function TableSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow p-6 animate-pulse space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="h-10 bg-gray-200 rounded" />
      ))}
    </div>
  )
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const [overview, setOverview] = useState<DashboardOverview | null>(null)
  const [videos, setVideos] = useState<VideoItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const handleSignOut = () => {
    localStorage.removeItem('jwt')
    navigate('/', { replace: true })
  }

  useEffect(() => {
    Promise.all([getOverview(), getTopVideos()])
      .then(([ov, vids]) => {
        setOverview(ov)
        setVideos(vids)
      })
      .catch((err) => {
        const msg =
          err?.response?.data?.detail ?? err?.message ?? 'Failed to load dashboard data.'
        setError(String(msg))
      })
      .finally(() => setIsLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-800">YouTube Analytics</h1>
          <button
            onClick={handleSignOut}
            className="text-sm text-gray-500 hover:text-gray-800 transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8 space-y-8">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
            {error}
          </div>
        )}

        {/* KPI Cards */}
        <section>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Channel Overview
            {overview && (
              <span className="ml-2 normal-case font-normal text-gray-400">
                · {overview.snapshot_date} ({overview.data_source})
              </span>
            )}
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {isLoading ? (
              Array.from({ length: 4 }).map((_, i) => <KpiSkeleton key={i} />)
            ) : overview ? (
              <>
                <KpiCard label="Subscribers" value={overview.kpis.subscriber_count} />
                <KpiCard label="Total Views" value={overview.kpis.total_views} />
                <KpiCard
                  label="Watch Time"
                  value={overview.kpis.watch_time_minutes.toLocaleString()}
                  unit="min"
                />
                <KpiCard label="Videos" value={overview.kpis.video_count} />
              </>
            ) : null}
          </div>
        </section>

        {/* Top Videos */}
        <section>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Top 5 Videos
          </h2>
          {isLoading ? (
            <TableSkeleton />
          ) : videos.length > 0 ? (
            <TopVideosTable videos={videos} />
          ) : (
            !error && (
              <p className="text-gray-500 text-sm">No video data available.</p>
            )
          )}
        </section>
      </main>
    </div>
  )
}
