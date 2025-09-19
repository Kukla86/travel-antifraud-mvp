import { useState, useEffect } from 'react'

const RiskChart = ({ data, title }) => {
  const [animatedData, setAnimatedData] = useState({ low: 0, medium: 0, high: 0 })
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true)
    }, 300)

    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    if (isVisible && data) {
      const duration = 2000
      const steps = 60
      const increment = {
        low: data.low / steps,
        medium: data.medium / steps,
        high: data.high / steps
      }
      
      let current = { low: 0, medium: 0, high: 0 }

      const timer = setInterval(() => {
        current.low += increment.low
        current.medium += increment.medium
        current.high += increment.high

        if (current.low >= data.low && current.medium >= data.medium && current.high >= data.high) {
          setAnimatedData(data)
          clearInterval(timer)
        } else {
          setAnimatedData({
            low: Math.floor(current.low),
            medium: Math.floor(current.medium),
            high: Math.floor(current.high)
          })
        }
      }, duration / steps)

      return () => clearInterval(timer)
    }
  }, [isVisible, data])

  const total = animatedData.low + animatedData.medium + animatedData.high
  const percentages = total > 0 ? {
    low: (animatedData.low / total) * 100,
    medium: (animatedData.medium / total) * 100,
    high: (animatedData.high / total) * 100
  } : { low: 0, medium: 0, high: 0 }

  const chartData = [
    {
      label: 'Low Risk',
      value: animatedData.low,
      percentage: percentages.low,
      color: 'emerald',
      gradient: 'from-emerald-500 to-green-500',
      textColor: 'text-emerald-400',
      bgColor: 'bg-emerald-500/20'
    },
    {
      label: 'Medium Risk',
      value: animatedData.medium,
      percentage: percentages.medium,
      color: 'amber',
      gradient: 'from-amber-500 to-orange-500',
      textColor: 'text-amber-400',
      bgColor: 'bg-amber-500/20'
    },
    {
      label: 'High Risk',
      value: animatedData.high,
      percentage: percentages.high,
      color: 'red',
      gradient: 'from-red-500 to-pink-500',
      textColor: 'text-red-400',
      bgColor: 'bg-red-500/20'
    }
  ]

  return (
    <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 overflow-hidden">
      <div className="px-8 py-6 border-b border-gray-700/50">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-semibold text-white">{title}</h3>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span className="text-gray-400 text-sm">Live Data</span>
          </div>
        </div>
      </div>
      
      <div className="p-8">
        <div className="grid grid-cols-3 gap-8">
          {chartData.map((item, index) => (
            <div key={item.label} className="text-center group">
              <div className="relative w-24 h-24 mx-auto mb-4">
                {/* Background circle */}
                <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                  <circle 
                    cx="50" 
                    cy="50" 
                    r="40" 
                    stroke="currentColor" 
                    strokeWidth="8" 
                    fill="none" 
                    className="text-gray-700"
                  />
                  {/* Progress circle */}
                  <circle 
                    cx="50" 
                    cy="50" 
                    r="40" 
                    stroke="currentColor" 
                    strokeWidth="8" 
                    fill="none" 
                    strokeDasharray={`${isVisible ? (item.percentage * 2.51) : 0} 251`}
                    className={`text-${item.color}-500 transition-all duration-2000 ease-out`}
                    style={{
                      strokeDashoffset: 0,
                      strokeLinecap: 'round'
                    }}
                  />
                </svg>
                
                {/* Center value */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className={`text-2xl font-bold ${item.textColor} transition-all duration-500 ${isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-75'}`}>
                    {item.value}
                  </span>
                </div>
              </div>
              
              <div className={`${item.textColor} text-lg font-semibold mb-1`}>
                {item.label}
              </div>
              <div className="text-gray-500 text-sm">
                {item.percentage.toFixed(1)}% of total
              </div>
              
              {/* Animated bar */}
              <div className="mt-3 w-full bg-gray-700/50 rounded-full h-1 overflow-hidden">
                <div 
                  className={`h-full bg-gradient-to-r ${item.gradient} rounded-full transition-all duration-2000 ease-out`}
                  style={{ 
                    width: isVisible ? `${item.percentage}%` : '0%' 
                  }}
                />
              </div>
            </div>
          ))}
        </div>
        
        {/* Summary stats */}
        <div className="mt-8 grid grid-cols-3 gap-6">
          {chartData.map((item) => (
            <div key={`summary-${item.label}`} className={`${item.bgColor} rounded-xl p-4 border border-${item.color}-500/30`}>
              <div className="flex items-center justify-between">
                <span className={`${item.textColor} text-sm font-medium`}>{item.label}</span>
                <span className={`${item.textColor} text-lg font-bold`}>{item.value}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default RiskChart
