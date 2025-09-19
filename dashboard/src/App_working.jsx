import { useEffect, useState } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8000'
const API_KEY = 'antifraud_dev_key_2024'

function App() {
  const [checks, setChecks] = useState([])
  const [loading, setLoading] = useState(true)
  const [metrics, setMetrics] = useState({})
  const [analytics, setAnalytics] = useState({})
  const [filters, setFilters] = useState({
    email: '',
    ip: '',
    riskMin: '',
    riskMax: ''
  })

  // Загрузка данных
  const loadData = async () => {
    try {
      setLoading(true)
      
      // Загружаем проверки
      const checksResponse = await fetch(`${API_BASE}/api/checks?limit=50`, {
        headers: { 'X-API-Key': API_KEY }
      })
      const checksData = await checksResponse.json()
      setChecks(checksData)

      // Загружаем метрики
      const metricsResponse = await fetch(`${API_BASE}/api/metrics`)
      const metricsData = await metricsResponse.json()
      setMetrics(metricsData)

      // Загружаем аналитику
      const analyticsResponse = await fetch(`${API_BASE}/api/analytics/risk-distribution`)
      const analyticsData = await analyticsResponse.json()
      setAnalytics(analyticsData)

    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 30000) // Обновляем каждые 30 секунд
    return () => clearInterval(interval)
  }, [])

  // Фильтрация проверок
  const filteredChecks = checks.filter(check => {
    if (filters.email && !check.email?.toLowerCase().includes(filters.email.toLowerCase())) return false
    if (filters.ip && !check.ip?.includes(filters.ip)) return false
    if (filters.riskMin && check.risk_score < parseInt(filters.riskMin)) return false
    if (filters.riskMax && check.risk_score > parseInt(filters.riskMax)) return false
    return true
  })

  // Получение цвета для уровня риска
  const getRiskColor = (score) => {
    if (score < 30) return 'text-green-600 bg-green-100'
    if (score < 70) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  // Получение рекомендации
  const getRecommendation = (score) => {
    if (score < 30) return 'Allow'
    if (score < 70) return 'Review'
    return 'Block'
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading antifraud dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Travel Antifraud Dashboard</h1>
              <p className="text-gray-600">Real-time fraud detection and monitoring</p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500">Last updated: {new Date().toLocaleTimeString()}</div>
              <div className="text-sm text-green-600">● System Online</div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Checks</p>
                <p className="text-2xl font-semibold text-gray-900">{metrics.total_checks || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">High Risk</p>
                <p className="text-2xl font-semibold text-gray-900">{metrics.high_risk_checks || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Blacklisted IPs</p>
                <p className="text-2xl font-semibold text-gray-900">{metrics.blacklisted_ips || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Connections</p>
                <p className="text-2xl font-semibold text-gray-900">{metrics.active_connections || 0}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Risk Distribution */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Risk Distribution</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">{analytics.low || 0}</div>
                <div className="text-sm text-gray-600">Low Risk</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-600">{analytics.medium || 0}</div>
                <div className="text-sm text-gray-600">Medium Risk</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-red-600">{analytics.high || 0}</div>
                <div className="text-sm text-gray-600">High Risk</div>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Filters</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <input
                  type="text"
                  value={filters.email}
                  onChange={(e) => setFilters({...filters, email: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Filter by email..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">IP Address</label>
                <input
                  type="text"
                  value={filters.ip}
                  onChange={(e) => setFilters({...filters, ip: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Filter by IP..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Min Risk Score</label>
                <input
                  type="number"
                  value={filters.riskMin}
                  onChange={(e) => setFilters({...filters, riskMin: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Max Risk Score</label>
                <input
                  type="number"
                  value={filters.riskMax}
                  onChange={(e) => setFilters({...filters, riskMax: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="100"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Checks Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Fraud Checks ({filteredChecks.length})</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">BIN</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Flags</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredChecks.map((check) => (
                  <tr key={check.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      #{check.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {check.email || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {check.ip || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {check.bin || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRiskColor(check.risk_score)}`}>
                          {check.risk_score}% - {getRecommendation(check.risk_score)}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-wrap gap-1">
                        {check.fraud_flags?.map((flag, index) => (
                          <span key={index} className="inline-flex px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded">
                            {flag}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {check.created_at ? new Date(check.created_at).toLocaleString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
