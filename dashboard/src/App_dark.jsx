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
    if (score < 30) return 'text-emerald-400 bg-emerald-900/20 border-emerald-500/30'
    if (score < 70) return 'text-amber-400 bg-amber-900/20 border-amber-500/30'
    return 'text-red-400 bg-red-900/20 border-red-500/30'
  }

  // Получение рекомендации
  const getRecommendation = (score) => {
    if (score < 30) return 'Allow'
    if (score < 70) return 'Review'
    return 'Block'
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-8 h-8 bg-cyan-500/20 rounded-full animate-pulse"></div>
            </div>
          </div>
          <p className="mt-6 text-gray-400 text-lg font-medium">Loading antifraud dashboard...</p>
          <p className="mt-2 text-gray-500 text-sm">Analyzing security patterns</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800/50 backdrop-blur-xl border-b border-gray-700/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                  Travel Antifraud
                </h1>
                <p className="text-gray-400 text-sm">Real-time fraud detection & monitoring</p>
              </div>
            </div>
            <div className="flex items-center space-x-6">
              <div className="text-right">
                <div className="text-sm text-gray-400">Last updated</div>
                <div className="text-cyan-400 font-mono text-sm">{new Date().toLocaleTimeString()}</div>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                <span className="text-emerald-400 text-sm font-medium">System Online</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-8">
        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 hover:border-cyan-500/30 transition-all duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm font-medium mb-2">Total Checks</p>
                <p className="text-3xl font-bold text-white">{metrics.total_checks || 0}</p>
                <p className="text-emerald-400 text-xs mt-1">+12% from yesterday</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 hover:border-red-500/30 transition-all duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm font-medium mb-2">High Risk</p>
                <p className="text-3xl font-bold text-white">{metrics.high_risk_checks || 0}</p>
                <p className="text-red-400 text-xs mt-1">Requires attention</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-red-500/20 to-pink-500/20 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 hover:border-amber-500/30 transition-all duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm font-medium mb-2">Blacklisted IPs</p>
                <p className="text-3xl font-bold text-white">{metrics.blacklisted_ips || 0}</p>
                <p className="text-amber-400 text-xs mt-1">Blocked addresses</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-amber-500/20 to-orange-500/20 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 hover:border-emerald-500/30 transition-all duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm font-medium mb-2">Active Connections</p>
                <p className="text-3xl font-bold text-white">{metrics.active_connections || 0}</p>
                <p className="text-emerald-400 text-xs mt-1">Live monitoring</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500/20 to-green-500/20 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Risk Distribution Chart */}
        <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 mb-8 overflow-hidden">
          <div className="px-8 py-6 border-b border-gray-700/50">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold text-white">Risk Distribution</h3>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
                <span className="text-gray-400 text-sm">Live Data</span>
              </div>
            </div>
          </div>
          <div className="p-8">
            <div className="grid grid-cols-3 gap-8">
              <div className="text-center group">
                <div className="relative w-24 h-24 mx-auto mb-4">
                  <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="8" fill="none" className="text-gray-700"/>
                    <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="8" fill="none" 
                            strokeDasharray={`${(analytics.low || 0) * 2.5} 251`} 
                            className="text-emerald-500 transition-all duration-1000 ease-out"/>
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold text-emerald-400">{analytics.low || 0}</span>
                  </div>
                </div>
                <div className="text-emerald-400 text-lg font-semibold">Low Risk</div>
                <div className="text-gray-500 text-sm">Safe transactions</div>
              </div>
              
              <div className="text-center group">
                <div className="relative w-24 h-24 mx-auto mb-4">
                  <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="8" fill="none" className="text-gray-700"/>
                    <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="8" fill="none" 
                            strokeDasharray={`${(analytics.medium || 0) * 2.5} 251`} 
                            className="text-amber-500 transition-all duration-1000 ease-out"/>
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold text-amber-400">{analytics.medium || 0}</span>
                  </div>
                </div>
                <div className="text-amber-400 text-lg font-semibold">Medium Risk</div>
                <div className="text-gray-500 text-sm">Review required</div>
              </div>
              
              <div className="text-center group">
                <div className="relative w-24 h-24 mx-auto mb-4">
                  <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="8" fill="none" className="text-gray-700"/>
                    <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="8" fill="none" 
                            strokeDasharray={`${(analytics.high || 0) * 2.5} 251`} 
                            className="text-red-500 transition-all duration-1000 ease-out"/>
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold text-red-400">{analytics.high || 0}</span>
                  </div>
                </div>
                <div className="text-red-400 text-lg font-semibold">High Risk</div>
                <div className="text-gray-500 text-sm">Block immediately</div>
              </div>
            </div>
          </div>
        </div>

        {/* Advanced Filters */}
        <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 mb-8">
          <div className="px-8 py-6 border-b border-gray-700/50">
            <div className="flex items-center space-x-3">
              <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z" />
              </svg>
              <h3 className="text-xl font-semibold text-white">Advanced Filters</h3>
            </div>
          </div>
          <div className="p-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">Email Address</label>
                <div className="relative">
                  <input
                    type="text"
                    value={filters.email}
                    onChange={(e) => setFilters({...filters, email: e.target.value})}
                    className="w-full px-4 py-3 bg-gray-800/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all duration-200"
                    placeholder="Filter by email..."
                  />
                  <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                </div>
              </div>
              
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">IP Address</label>
                <div className="relative">
                  <input
                    type="text"
                    value={filters.ip}
                    onChange={(e) => setFilters({...filters, ip: e.target.value})}
                    className="w-full px-4 py-3 bg-gray-800/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all duration-200"
                    placeholder="Filter by IP..."
                  />
                  <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                </div>
              </div>
              
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">Min Risk Score</label>
                <input
                  type="number"
                  value={filters.riskMin}
                  onChange={(e) => setFilters({...filters, riskMin: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-800/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all duration-200"
                  placeholder="0"
                />
              </div>
              
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">Max Risk Score</label>
                <input
                  type="number"
                  value={filters.riskMax}
                  onChange={(e) => setFilters({...filters, riskMax: e.target.value})}
                  className="w-full px-4 py-3 bg-gray-800/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all duration-200"
                  placeholder="100"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Fraud Checks Table */}
        <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 overflow-hidden">
          <div className="px-8 py-6 border-b border-gray-700/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <h3 className="text-xl font-semibold text-white">Fraud Checks</h3>
                <span className="px-3 py-1 bg-cyan-500/20 text-cyan-400 text-sm font-medium rounded-full">
                  {filteredChecks.length} results
                </span>
              </div>
              <button className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-sm font-medium rounded-xl hover:from-cyan-600 hover:to-blue-700 transition-all duration-200">
                Export Data
              </button>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-800/30">
                <tr>
                  <th className="px-8 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">ID</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">Email</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">IP</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">BIN</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">Risk Score</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">Flags</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/50">
                {filteredChecks.map((check, index) => (
                  <tr key={check.id} className="hover:bg-gray-800/30 transition-colors duration-200 group">
                    <td className="px-8 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-lg flex items-center justify-center">
                          <span className="text-cyan-400 font-mono text-sm font-bold">#{check.id}</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-white font-medium">{check.email || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-gray-300 font-mono text-sm">{check.ip || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-gray-300 font-mono text-sm">{check.bin || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-3">
                        <div className={`px-3 py-1 rounded-full border text-sm font-semibold ${getRiskColor(check.risk_score)}`}>
                          {check.risk_score}% - {getRecommendation(check.risk_score)}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-2">
                        {check.fraud_flags?.map((flag, flagIndex) => (
                          <span key={flagIndex} className="px-2 py-1 bg-red-500/20 text-red-400 text-xs font-medium rounded-lg border border-red-500/30">
                            {flag}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-gray-400 text-sm">
                        {check.created_at ? new Date(check.created_at).toLocaleString() : '-'}
                      </div>
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
