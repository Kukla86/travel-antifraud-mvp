import { useState, useEffect } from 'react'

const AnimatedMetric = ({ value, label, icon, color, trend, delay = 0 }) => {
  const [displayValue, setDisplayValue] = useState(0)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true)
    }, delay)

    return () => clearTimeout(timer)
  }, [delay])

  useEffect(() => {
    if (isVisible) {
      const duration = 2000
      const steps = 60
      const increment = value / steps
      let current = 0

      const timer = setInterval(() => {
        current += increment
        if (current >= value) {
          setDisplayValue(value)
          clearInterval(timer)
        } else {
          setDisplayValue(Math.floor(current))
        }
      }, duration / steps)

      return () => clearInterval(timer)
    }
  }, [isVisible, value])

  const getColorClasses = (color) => {
    switch (color) {
      case 'cyan':
        return {
          bg: 'from-cyan-500/20 to-blue-500/20',
          text: 'text-cyan-400',
          icon: 'text-cyan-400'
        }
      case 'red':
        return {
          bg: 'from-red-500/20 to-pink-500/20',
          text: 'text-red-400',
          icon: 'text-red-400'
        }
      case 'amber':
        return {
          bg: 'from-amber-500/20 to-orange-500/20',
          text: 'text-amber-400',
          icon: 'text-amber-400'
        }
      case 'emerald':
        return {
          bg: 'from-emerald-500/20 to-green-500/20',
          text: 'text-emerald-400',
          icon: 'text-emerald-400'
        }
      default:
        return {
          bg: 'from-gray-500/20 to-gray-600/20',
          text: 'text-gray-400',
          icon: 'text-gray-400'
        }
    }
  }

  const colors = getColorClasses(color)

  return (
    <div className={`bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 hover:border-${color}-500/30 transition-all duration-300 group`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-gray-400 text-sm font-medium mb-2">{label}</p>
          <p className={`text-3xl font-bold text-white transition-all duration-500 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
            {displayValue.toLocaleString()}
          </p>
          {trend && (
            <p className={`${colors.text} text-xs mt-1 flex items-center space-x-1`}>
              <span className={trend > 0 ? 'text-emerald-400' : 'text-red-400'}>
                {trend > 0 ? '↗' : '↘'}
              </span>
              <span>{Math.abs(trend)}% from yesterday</span>
            </p>
          )}
        </div>
        <div className={`w-12 h-12 bg-gradient-to-br ${colors.bg} rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
          {icon}
        </div>
      </div>
      
      {/* Animated progress bar */}
      <div className="mt-4 w-full bg-gray-700/50 rounded-full h-1 overflow-hidden">
        <div 
          className={`h-full bg-gradient-to-r ${colors.bg.replace('/20', '/60')} rounded-full transition-all duration-2000 ease-out`}
          style={{ 
            width: isVisible ? `${Math.min((displayValue / value) * 100, 100)}%` : '0%' 
          }}
        />
      </div>
    </div>
  )
}

export default AnimatedMetric
