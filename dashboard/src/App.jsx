import { useEffect, useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const API_KEY = import.meta.env.VITE_API_KEY || 'antifraud_dev_key_2024'

function App() {
  const [checks, setChecks] = useState([])
  const [loading, setLoading] = useState(true)
  const [metrics, setMetrics] = useState({})
  const [analytics, setAnalytics] = useState({})
  const [selectedCheck, setSelectedCheck] = useState(null)
  const [filters, setFilters] = useState({
    email: '',
    ip: '',
    riskMin: '',
    riskMax: '',
    status: ''
  })
  const [activeTab, setActiveTab] = useState('overview')

  // Загрузка данных
  const loadData = async () => {
    try {
      setLoading(true)
      
      const checksResponse = await fetch(`${API_BASE}/api/checks?limit=100`, {
        headers: { 'X-API-Key': API_KEY }
      })
      const checksData = await checksResponse.json()
      setChecks(checksData)

      const metricsResponse = await fetch(`${API_BASE}/api/metrics`)
      const metricsData = await metricsResponse.json()
      setMetrics(metricsData)

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
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [])

  // Фильтрация проверок
  const filteredChecks = checks.filter(check => {
    if (filters.email && !check.email?.toLowerCase().includes(filters.email.toLowerCase())) return false
    if (filters.ip && !check.ip?.includes(filters.ip)) return false
    if (filters.riskMin && check.risk_score < parseInt(filters.riskMin)) return false
    if (filters.riskMax && check.risk_score > parseInt(filters.riskMax)) return false
    if (filters.status && getRecommendation(check.risk_score).toLowerCase() !== filters.status.toLowerCase()) return false
    return true
  })

  // Получение цвета для уровня риска
  const getRiskColor = (score) => {
    if (score < 30) return 'success'
    if (score < 70) return 'warning'
    return 'danger'
  }

  // Получение рекомендации
  const getRecommendation = (score) => {
    if (score < 30) return 'Allow'
    if (score < 70) return 'Review'
    return 'Block'
  }

  // Получение цвета для бейджа
  const getBadgeColor = (type) => {
    switch(type) {
      case 'success': return '#10b981'
      case 'warning': return '#f59e0b'
      case 'danger': return '#ef4444'
      default: return '#6b7280'
    }
  }

  // Получение фона для бейджа
  const getBadgeBg = (type) => {
    switch(type) {
      case 'success': return '#065f46'
      case 'warning': return '#92400e'
      case 'danger': return '#991b1b'
      default: return '#374151'
    }
  }

  // Статистика для графиков
  const getChartData = () => {
    const last7Days = []
    const today = new Date()
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(date.getDate() - i)
      const dayChecks = checks.filter(check => {
        const checkDate = new Date(check.created_at)
        return checkDate.toDateString() === date.toDateString()
      })
      last7Days.push({
        date: date.toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' }),
        checks: dayChecks.length,
        highRisk: dayChecks.filter(c => c.risk_score >= 70).length
      })
    }
    return last7Days
  }

  const chartData = getChartData()

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    )
  }

  return (
    <div className="dashboard-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <div className="logo-icon"></div>
            <span>Antifraud</span>
          </div>
        </div>
        
        <nav className="sidebar-nav">
          <div className="nav-item active" onClick={() => setActiveTab('overview')}>
            <div className="nav-icon">📊</div>
            <span>Overview</span>
          </div>
          <div className="nav-item" onClick={() => setActiveTab('logs')}>
            <div className="nav-icon">📋</div>
            <span>Fraud Logs</span>
          </div>
          <div className="nav-item" onClick={() => setActiveTab('analytics')}>
            <div className="nav-icon">📈</div>
            <span>Analytics</span>
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className="user-profile">
            <div className="user-avatar">JC</div>
            <div className="user-info">
              <div className="user-name">John Carter</div>
              <div className="user-role">Admin</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {/* Header */}
        <header className="main-header">
          <div className="header-left">
            <h1>Welcome back, John</h1>
            <p>Here's what's happening with your fraud detection system</p>
          </div>
          <div className="header-right">
            <button className="btn btn-secondary">Export Data</button>
            <button className="btn btn-primary">Create Report</button>
          </div>
        </header>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="overview-content">
            {/* Metrics Cards */}
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-header">
                  <h3>Total Checks</h3>
                  <div className="metric-trend positive">+12%</div>
                </div>
                <div className="metric-value">{metrics.total_checks || 0}</div>
                <div className="metric-subtitle">Last 30 days</div>
              </div>

              <div className="metric-card">
                <div className="metric-header">
                  <h3>High Risk</h3>
                  <div className="metric-trend negative">+8%</div>
                </div>
                <div className="metric-value">{metrics.high_risk_checks || 0}</div>
                <div className="metric-subtitle">Requires attention</div>
              </div>

              <div className="metric-card">
                <div className="metric-header">
                  <h3>Blocked IPs</h3>
                  <div className="metric-trend neutral">+2%</div>
                </div>
                <div className="metric-value">{metrics.blacklisted_ips || 0}</div>
                <div className="metric-subtitle">In blacklist</div>
              </div>

              <div className="metric-card">
                <div className="metric-header">
                  <h3>Success Rate</h3>
                  <div className="metric-trend positive">+5%</div>
                </div>
                <div className="metric-value">94.2%</div>
                <div className="metric-subtitle">Accurate detection</div>
              </div>
            </div>

            {/* Charts */}
            <div className="charts-grid">
              <div className="chart-card">
                <div className="chart-header">
                  <h3>Checks Trend</h3>
                  <div className="chart-period">Last 7 days</div>
                </div>
                <div className="chart-content">
                  <div className="line-chart">
                    {chartData.map((item, index) => (
                      <div key={index} className="chart-bar">
                        <div className="bar-fill" style={{ height: `${(item.checks / Math.max(...chartData.map(d => d.checks))) * 100}%` }}></div>
                        <div className="bar-label">{item.date}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="chart-card">
                <div className="chart-header">
                  <h3>Risk Distribution</h3>
                  <div className="chart-period">Current status</div>
                </div>
                <div className="chart-content">
                  <div className="donut-chart">
                    <div className="donut-center">
                      <div className="donut-value">{checks.length}</div>
                      <div className="donut-label">Total</div>
                    </div>
                  </div>
                  <div className="chart-legend">
                    <div className="legend-item">
                      <div className="legend-color" style={{ backgroundColor: '#10b981' }}></div>
                      <span>Low Risk ({analytics.low || 0})</span>
                    </div>
                    <div className="legend-item">
                      <div className="legend-color" style={{ backgroundColor: '#f59e0b' }}></div>
                      <span>Medium Risk ({analytics.medium || 0})</span>
                    </div>
                    <div className="legend-item">
                      <div className="legend-color" style={{ backgroundColor: '#ef4444' }}></div>
                      <span>High Risk ({analytics.high || 0})</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="activity-card">
              <div className="card-header">
                <h3>Recent Activity</h3>
                <button className="btn btn-sm btn-outline">View All</button>
              </div>
              <div className="activity-list">
                {checks.slice(0, 5).map((check) => (
                  <div key={check.id} className="activity-item" onClick={() => setSelectedCheck(check)}>
                    <div className="activity-icon">
                      <div className={`status-dot ${getRiskColor(check.risk_score)}`}></div>
                    </div>
                    <div className="activity-content">
                      <div className="activity-title">
                        Check #{check.id} - {check.email || 'Unknown email'}
                      </div>
                      <div className="activity-subtitle">
                        {check.ip} • {new Date(check.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="activity-badge">
                      <span className={`badge badge-${getRiskColor(check.risk_score)}`}>
                        {getRecommendation(check.risk_score)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Logs Tab */}
        {activeTab === 'logs' && (
          <div className="logs-content">
            {/* Filters */}
            <div className="filters-card">
              <div className="filters-grid">
                <div className="filter-group">
                  <label>Email</label>
                  <input
                    type="text"
                    value={filters.email}
                    onChange={(e) => setFilters({...filters, email: e.target.value})}
                    placeholder="Filter by email..."
                  />
                </div>
                <div className="filter-group">
                  <label>IP Address</label>
                  <input
                    type="text"
                    value={filters.ip}
                    onChange={(e) => setFilters({...filters, ip: e.target.value})}
                    placeholder="Filter by IP..."
                  />
                </div>
                <div className="filter-group">
                  <label>Risk Score</label>
                  <div className="range-inputs">
                    <input
                      type="number"
                      value={filters.riskMin}
                      onChange={(e) => setFilters({...filters, riskMin: e.target.value})}
                      placeholder="Min"
                    />
                    <span>to</span>
                    <input
                      type="number"
                      value={filters.riskMax}
                      onChange={(e) => setFilters({...filters, riskMax: e.target.value})}
                      placeholder="Max"
                    />
                  </div>
                </div>
                <div className="filter-group">
                  <label>Status</label>
                  <select
                    value={filters.status}
                    onChange={(e) => setFilters({...filters, status: e.target.value})}
                  >
                    <option value="">All</option>
                    <option value="allow">Allow</option>
                    <option value="review">Review</option>
                    <option value="block">Block</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Logs Table */}
            <div className="logs-table-card">
              <div className="table-header">
                <h3>Fraud Detection Logs</h3>
                <div className="table-actions">
                  <span className="results-count">{filteredChecks.length} results</span>
                  <button className="btn btn-sm btn-outline">Export</button>
                </div>
              </div>
              <div className="table-container">
                <table className="logs-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Email</th>
                      <th>IP Address</th>
                      <th>BIN</th>
                      <th>Risk Score</th>
                      <th>Flags</th>
                      <th>Date</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredChecks.map((check) => (
                      <tr key={check.id} onClick={() => setSelectedCheck(check)}>
                        <td className="id-cell">#{check.id}</td>
                        <td className="email-cell">{check.email || '-'}</td>
                        <td className="ip-cell">{check.ip || '-'}</td>
                        <td className="bin-cell">{check.bin || '-'}</td>
                        <td className="risk-cell">
                          <span className={`badge badge-${getRiskColor(check.risk_score)}`}>
                            {check.risk_score}%
                          </span>
                        </td>
                        <td className="flags-cell">
                          <div className="flags-list">
                            {check.fraud_flags?.slice(0, 2).map((flag, index) => (
                              <span key={index} className="flag-tag">{flag}</span>
                            ))}
                            {check.fraud_flags?.length > 2 && (
                              <span className="flag-more">+{check.fraud_flags.length - 2}</span>
                            )}
                          </div>
                        </td>
                        <td className="date-cell">
                          {check.created_at ? new Date(check.created_at).toLocaleString() : '-'}
                        </td>
                        <td className="actions-cell">
                          <button className="btn btn-sm btn-outline">View</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div className="analytics-content">
            <div className="analytics-grid">
              <div className="analytics-card">
                <h3>Performance Metrics</h3>
                <div className="metrics-list">
                  <div className="metric-item">
                    <span className="metric-label">Detection Accuracy</span>
                    <span className="metric-value">94.2%</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">False Positives</span>
                    <span className="metric-value">5.8%</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Average Response Time</span>
                    <span className="metric-value">1.2s</span>
                  </div>
                </div>
              </div>
              
              <div className="analytics-card">
                <h3>Top Fraud Flags</h3>
                <div className="flags-stats">
                  <div className="flag-stat">
                    <span className="flag-name">Temporary Email</span>
                    <div className="flag-bar">
                      <div className="flag-fill" style={{ width: '85%' }}></div>
                    </div>
                    <span className="flag-count">85%</span>
                  </div>
                  <div className="flag-stat">
                    <span className="flag-name">Geo Mismatch</span>
                    <div className="flag-bar">
                      <div className="flag-fill" style={{ width: '72%' }}></div>
                    </div>
                    <span className="flag-count">72%</span>
                  </div>
                  <div className="flag-stat">
                    <span className="flag-name">Bot Activity</span>
                    <div className="flag-bar">
                      <div className="flag-fill" style={{ width: '68%' }}></div>
                    </div>
                    <span className="flag-count">68%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Check Details Modal */}
      {selectedCheck && (
        <div className="modal-overlay" onClick={() => setSelectedCheck(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Check Details #{selectedCheck.id}</h3>
              <button className="modal-close" onClick={() => setSelectedCheck(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="details-grid">
                <div className="detail-group">
                  <label>Email</label>
                  <span>{selectedCheck.email || 'N/A'}</span>
                </div>
                <div className="detail-group">
                  <label>IP Address</label>
                  <span>{selectedCheck.ip || 'N/A'}</span>
                </div>
                <div className="detail-group">
                  <label>BIN</label>
                  <span>{selectedCheck.bin || 'N/A'}</span>
                </div>
                <div className="detail-group">
                  <label>Risk Score</label>
                  <span className={`badge badge-${getRiskColor(selectedCheck.risk_score)}`}>
                    {selectedCheck.risk_score}% - {getRecommendation(selectedCheck.risk_score)}
                  </span>
                </div>
                <div className="detail-group">
                  <label>User Agent</label>
                  <span className="ua-text">{selectedCheck.user_agent || 'N/A'}</span>
                </div>
                <div className="detail-group">
                  <label>Timezone</label>
                  <span>{selectedCheck.timezone || 'N/A'}</span>
                </div>
                <div className="detail-group">
                  <label>Browser Language</label>
                  <span>{selectedCheck.browser_language || 'N/A'}</span>
                </div>
                <div className="detail-group">
                  <label>Session Duration</label>
                  <span>{selectedCheck.session_duration || 'N/A'}s</span>
                </div>
                <div className="detail-group">
                  <label>Typing Speed</label>
                  <span>{selectedCheck.typing_speed || 'N/A'} WPM</span>
                </div>
                <div className="detail-group">
                  <label>First Click Time</label>
                  <span>{selectedCheck.first_click_time || 'N/A'}ms</span>
                </div>
                <div className="detail-group full-width">
                  <label>Fraud Flags</label>
                  <div className="flags-list">
                    {selectedCheck.fraud_flags?.map((flag, index) => (
                      <span key={index} className="flag-tag">{flag}</span>
                    ))}
                  </div>
                </div>
                <div className="detail-group full-width">
                  <label>Created At</label>
                  <span>{selectedCheck.created_at ? new Date(selectedCheck.created_at).toLocaleString() : 'N/A'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App