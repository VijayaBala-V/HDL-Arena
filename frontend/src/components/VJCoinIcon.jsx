import React from 'react'

/**
 * Custom VJ Coin Icon Component
 * 
 * Design:
 * - Circular coin outline with electric cyan (#00f3ff) & neon violet (#b026ff) gradient.
 * - Deep dark background (#070b14).
 * - Prominent, crisp "VJ" monogram centered inside.
 * - Subtle inner circular border and circuit dot accents.
 * - Interactive glow on hover and active states.
 */
export default function VJCoinIcon({
  size = 18,
  className = '',
  animate = false,
  glow = true,
  title = 'VJ Coin'
}) {
  const uniqueId = React.useId ? React.useId().replace(/:/g, '') : 'vj'
  const gradId = `vj-grad-${uniqueId}`
  const textGradId = `vj-text-grad-${uniqueId}`
  const filterId = `vj-glow-${uniqueId}`

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`vj-coin-svg ${animate ? 'vj-coin-animate' : ''} ${className}`}
      aria-label={title}
      role="img"
      style={{
        display: 'inline-block',
        verticalAlign: 'middle',
        flexShrink: 0
      }}
    >
      <title>{title}</title>
      <defs>
        {/* Outer Ring & Ridge Gradient */}
        <linearGradient id={gradId} x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#00f3ff" />
          <stop offset="45%" stopColor="#38bdf8" />
          <stop offset="75%" stopColor="#a855f7" />
          <stop offset="100%" stopColor="#b026ff" />
        </linearGradient>

        {/* VJ Text Gradient */}
        <linearGradient id={textGradId} x1="8" y1="8" x2="24" y2="24" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#ffffff" />
          <stop offset="50%" stopColor="#00f3ff" />
          <stop offset="100%" stopColor="#c084fc" />
        </linearGradient>

        {/* Subtle Glow Filter */}
        {glow && (
          <filter id={filterId} x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0" stdDeviation="1.5" floodColor="#00f3ff" floodOpacity="0.6" />
          </filter>
        )}
      </defs>

      {/* Outer Coin Base / Fill */}
      <circle cx="16" cy="16" r="14.5" fill="#070a14" stroke={`url(#${gradId})`} strokeWidth="1.8" filter={glow ? `url(#${filterId})` : undefined} />

      {/* Inner Decorative Ridge Ring */}
      <circle cx="16" cy="16" r="11.8" fill="none" stroke="rgba(0, 243, 255, 0.35)" strokeWidth="0.8" strokeDasharray="1.5 1.5" />

      {/* Decorative Core Circuit Dots */}
      <circle cx="16" cy="4.2" r="0.9" fill="#00f3ff" />
      <circle cx="16" cy="27.8" r="0.9" fill="#b026ff" />
      <circle cx="4.2" cy="16" r="0.9" fill="#00f3ff" />
      <circle cx="27.8" cy="16" r="0.9" fill="#b026ff" />

      {/* "VJ" Monogram Letters */}
      <text
        x="16"
        y="19.5"
        textAnchor="middle"
        fontFamily="'Plus Jakarta Sans', system-ui, -apple-system, sans-serif"
        fontSize="10.5"
        fontWeight="800"
        letterSpacing="-0.5px"
        fill={`url(#${textGradId})`}
        style={{
          filter: 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.9))'
        }}
      >
        VJ
      </text>
    </svg>
  )
}
