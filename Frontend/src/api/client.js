import axios from 'axios'
import { generateMockReports } from './mockData'

// ---------------------------------------------------------------------------
// SWITCH THIS FLAG WHEN THE BACKEND (Person 5's FastAPI) IS READY.
// Everything else in the app calls the functions below — nothing in your
// components needs to change when you flip this.
// ---------------------------------------------------------------------------
const USE_MOCK = false
const API_BASE_URL = 'http://localhost:8000' // update once backend is deployed

const httpClient = axios.create({ baseURL: API_BASE_URL, timeout: 8000 })

// Cache mock reports so the "live" feel is consistent across a session
let MOCK_CACHE = null
function getMockReports() {
  if (!MOCK_CACHE) MOCK_CACHE = generateMockReports(150)
  return MOCK_CACHE
}

/**
 * Fetch reports, optionally filtered.
 * filters: { eventTypes: string[], states: string[], verificationStatus: string,
 *            dateFrom: string, dateTo: string, search: string }
 */
export async function fetchReports(filters = {}) {
  if (USE_MOCK) {
    let data = getMockReports()

    if (filters.eventTypes?.length) {
      data = data.filter((r) => filters.eventTypes.includes(r.event_type))
    }
    if (filters.states?.length) {
      data = data.filter((r) => filters.states.includes(r.state))
    }
    if (filters.verificationStatus && filters.verificationStatus !== 'all') {
      data = data.filter((r) => r.verification_status === filters.verificationStatus)
    }
    if (filters.dateFrom) {
      data = data.filter((r) => new Date(r.timestamp) >= new Date(filters.dateFrom))
    }
    if (filters.dateTo) {
      data = data.filter((r) => new Date(r.timestamp) <= new Date(filters.dateTo))
    }
    if (filters.search) {
      const q = filters.search.toLowerCase()
      data = data.filter(
        (r) => r.city.toLowerCase().includes(q) || r.text.toLowerCase().includes(q),
      )
    }
    return data
  }

  // REAL BACKEND CALL — matches Person 5's planned FastAPI endpoint:
  // GET /reports?event_type=...&state=...&status=...&date_from=...&date_to=...&q=...
  const { data } = await httpClient.get('/reports', {
    params: {
      event_type: filters.eventTypes?.join(','),
      state: filters.states?.join(','),
      status: filters.verificationStatus,
      date_from: filters.dateFrom,
      date_to: filters.dateTo,
      q: filters.search,
    },
  })
  return data
}

/** Update a report's verification status — now represents a human ADMIN
 * OVERRIDE of the ML model's original call, not the primary verification
 * mechanism. Tags the change with verified_by: 'admin' so the audit trail
 * (and the Admin Panel UI) can distinguish ML-assessed reports from ones a
 * person has actually reviewed. */
export async function updateReportStatus(reportId, newStatus) {
  if (USE_MOCK) {
    const data = getMockReports()
    const report = data.find((r) => r.id === reportId)
    if (report) {
      report.verification_status = newStatus
      report.verified_by = 'admin'
    }
    return report
  }

  const { data } = await httpClient.patch(`/reports/${reportId}`, {
    verification_status: newStatus,
    verified_by: 'admin',
  })
  return data
}

/** Aggregated stats for the top ticker / stat cards */
export async function fetchStats() {
  if (USE_MOCK) {
    const data = getMockReports()
    const verified = data.filter((r) => r.verification_status === 'verified').length
    const critical = data.filter(
      (r) => ['flooding', 'thunderstorm'].includes(r.event_type) && r.credibility_score > 60,
    ).length
    const byState = {}
    data.forEach((r) => {
      byState[r.state] = (byState[r.state] || 0) + 1
    })
    const topState = Object.entries(byState).sort((a, b) => b[1] - a[1])[0]

    return {
      total: data.length,
      verifiedPct: Math.round((verified / data.length) * 100),
      activeAlerts: critical,
      mostAffectedState: topState ? topState[0] : '—',
    }
  }

  const { data } = await httpClient.get('/stats')
  return data
}
