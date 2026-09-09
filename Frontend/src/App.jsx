import { useEffect, useState, useCallback } from 'react'
import TopBar from './components/TopBar'
import HeaderFilters from './components/HeaderFilters'
import LeftStatsRail from './components/LeftStatsRail'
import MapView from './components/MapView'
import AnalyticsHeadline from './components/AnalyticsHeadline'
import ReportFeed from './components/ReportFeed'
import AdminTable from './components/AdminTable'
import { fetchReports, fetchStats } from './api/client'

const DEFAULT_FILTERS = {
  eventTypes: [],
  verificationStatus: 'all',
  dateFrom: '',
  dateTo: '',
  search: '',
}

export default function App() {
  const [view, setView] = useState('dashboard')
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [reports, setReports] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadData = useCallback(async () => {
    setLoading(true)
    const [reportData, statData] = await Promise.all([fetchReports(filters), fetchStats()])
    setReports(reportData)
    setStats(statData)
    setLoading(false)
  }, [filters])

  useEffect(() => {
    loadData()
  }, [loadData])

  return (
    <div className="min-h-screen flex flex-col font-body bg-void">
      <TopBar view={view} setView={setView} />
      <HeaderFilters filters={filters} setFilters={setFilters} />

      <div className="flex flex-1 overflow-hidden">
        <LeftStatsRail stats={stats} />

        <main className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
          {loading && <p className="text-xs text-text-muted font-mono">Loading reports...</p>}

          {view === 'dashboard' ? (
            <>
              <MapView reports={reports} searchQuery={filters.search} />
              <AnalyticsHeadline reports={reports} />
              <ReportFeed reports={reports} />
            </>
          ) : (
            <AdminTable reports={reports} onUpdate={loadData} />
          )}
        </main>
      </div>
    </div>
  )
}
