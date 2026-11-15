import React, { useState, useMemo, useRef, useEffect } from 'react'

/**
 * Parses a raw VCD string into structured timescale, maxTime, and signals array.
 * Correctly obtains vector bus widths, scopes, and ranges from VCD declarations.
 */
function parseVcdText(vcd) {
  if (!vcd || typeof vcd !== 'string' || !vcd.trim()) return null

  const variables = {}
  const signalEvents = {}
  const scopes = []
  let currentTime = 0
  let maxTime = 1
  let timescale = '1ns'

  for (const rawLine of vcd.split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line) continue

    if (line.startsWith('$timescale')) {
      const match = line.match(/\$timescale\s+([0-9]+\s*[a-zA-Z]+)/)
      if (match) timescale = match[1].replace(/\s+/g, '')
      continue
    }
    if (line.startsWith('$scope')) {
      const parts = line.split(/\s+/)
      if (parts.length >= 3) scopes.push(parts[2])
      continue
    }
    if (line.startsWith('$upscope')) {
      if (scopes.length > 0) scopes.pop()
      continue
    }
    if (line.startsWith('$var')) {
      const parts = line.split(/\s+/)
      const width = Number(parts[2]) || 1
      const id = parts[3]
      const name = parts[4]
      const range = parts.slice(5).find(p => p.startsWith('[')) || ''
      const scopeStr = scopes.join('.')
      const fullName = scopeStr ? `${scopeStr}.${name}` : name

      variables[id] = {
        name,
        fullName,
        scope: scopeStr,
        width,
        range: range || (width > 1 ? `[${width - 1}:0]` : ''),
        isBus: width > 1
      }
      if (!signalEvents[fullName]) {
        signalEvents[fullName] = []
      }
      continue
    }
    if (line.startsWith('#')) {
      currentTime = Number(line.slice(1)) || 0
      if (currentTime > maxTime) maxTime = currentTime
      continue
    }

    const scalar = line.match(/^([01xXzZ])(\S+)$/)
    const vector = line.match(/^[bB]([01xXzZ]+)\s+(\S+)$/)

    if (scalar && variables[scalar[2]]) {
      const v = variables[scalar[2]]
      signalEvents[v.fullName].push({
        time: currentTime,
        value: scalar[1].toLowerCase()
      })
    } else if (vector && variables[vector[2]]) {
      const v = variables[vector[2]]
      signalEvents[v.fullName].push({
        time: currentTime,
        value: vector[1].toLowerCase()
      })
    }
  }

  const rawSignals = []
  const seen = new Set()

  Object.keys(signalEvents).forEach(full => {
    const info = Object.values(variables).find(v => v.fullName === full)
    const baseName = full.split('.').pop()
    const key = `${info?.scope || ''}_${baseName}`
    if (seen.has(key)) return
    seen.add(key)

    rawSignals.push({
      fullName: full,
      name: baseName,
      scope: info?.scope || '',
      width: info?.width || 1,
      range: info?.range || '',
      isBus: (info?.width || 1) > 1,
      events: signalEvents[full] || []
    })
  })

  return { timescale, maxTime: Math.max(maxTime, 1), signals: rawSignals }
}

/**
 * Determines whether a signal is an Input or Output.
 */
function isSignalOutput(sig, ports = []) {
  const nameLower = sig.name.toLowerCase()
  const portMatch = ports.find(p => p.name.toLowerCase() === nameLower)
  if (portMatch) {
    return portMatch.direction?.toLowerCase() === 'output'
  }
  if (nameLower.startsWith('out') || nameLower === 'dout' || nameLower === 'q' || nameLower === 'count' || nameLower === 'y' || nameLower === 'valid' || nameLower === 'ready') {
    return true
  }
  return false
}

/**
 * ONE Unified Waveform Viewer
 * Combines Golden Wave (Input), Golden Wave (Output), Match or Not (Single Bit),
 * and Your Wave (Output) inside a single synchronized viewer container.
 */
export default function WaveformViewer({
  vcd,
  goldenVcd,
  goldenAvailable = false,
  targetTime = null,
  testResults = [],
  cycleLogs = [],
  verdict = null,
  ports = [],
  onJumpToTime = null
}) {
  const [radix, setRadix] = useState('hex') // 'hex' | 'dec' | 'bin' | 'ascii'
  const [zoom, setZoom] = useState(1.0)
  const [cursorTime, setCursorTime] = useState(null)
  const [filterQuery, setFilterQuery] = useState('')
  const [expandedBuses, setExpandedBuses] = useState({})
  const [showMinimap, setShowMinimap] = useState(true)

  const scrollerRef = useRef(null)
  const minimapRef = useRef(null)

  // Sync cursor when targetTime is jumped to
  useEffect(() => {
    if (targetTime !== null && targetTime !== undefined) {
      setCursorTime(targetTime)
    }
  }, [targetTime])

  // Parse User (Your) Waveform
  const yourParsed = useMemo(() => parseVcdText(vcd), [vcd])

  // Parse Golden Waveform
  const goldenParsed = useMemo(() => parseVcdText(goldenVcd), [goldenVcd])

  // Compute common timescale and maxTime
  const maxTime = useMemo(() => {
    const t1 = yourParsed?.maxTime || 1
    const t2 = goldenParsed?.maxTime || 1
    return Math.max(t1, t2)
  }, [yourParsed, goldenParsed])

  const timescale = yourParsed?.timescale || goldenParsed?.timescale || '1ns'

  // Extract assertion mismatches from cycle logs
  const mismatches = useMemo(() => {
    if (!Array.isArray(cycleLogs)) return []
    return cycleLogs.filter(c => c && c.match === false && c.time_num !== undefined)
  }, [cycleLogs])

  // First divergence timestamp
  const firstDivergenceTime = useMemo(() => {
    if (targetTime !== null && targetTime !== undefined) return targetTime
    if (mismatches.length > 0) return mismatches[0].time_num
    const failedTest = testResults.find(t => t.status === 'FAILED')
    if (failedTest && failedTest.time_ns !== undefined) return failedTest.time_ns
    return null
  }, [targetTime, mismatches, testResults])

  // Format value according to selected radix
  function formatValue(val, isBus) {
    if (!val) return '-'
    if (!isBus) return val.toUpperCase()
    if (/[xz]/i.test(val)) return val.toUpperCase()

    const dec = parseInt(val, 2)
    if (isNaN(dec)) return val.toUpperCase()

    if (radix === 'hex') return '0x' + dec.toString(16).toUpperCase()
    if (radix === 'dec') return dec.toString(10)
    if (radix === 'bin') return val
    if (radix === 'ascii') {
      try {
        return (dec >= 32 && dec <= 126) ? `'${String.fromCharCode(dec)}'` : '0x' + dec.toString(16).toUpperCase()
      } catch (e) {
        return '0x' + dec.toString(16).toUpperCase()
      }
    }
    return val
  }

  function getValueAtTime(events, t) {
    if (!events || events.length === 0) return 'x'
    let current = events[0].value
    for (const ev of events) {
      if (ev.time <= t) current = ev.value
      else break
    }
    return current
  }

  // Helper to expand buses
  function expandSignals(signalsList) {
    const result = []
    signalsList.forEach(sig => {
      if (filterQuery && !sig.name.toLowerCase().includes(filterQuery.toLowerCase())) {
        return
      }
      result.push(sig)

      if (sig.isBus && expandedBuses[sig.fullName]) {
        for (let bit = sig.width - 1; bit >= 0; bit--) {
          const bitEvents = sig.events.map(ev => {
            let bitVal = '0'
            const rawVal = ev.value
            if (/[xz]/i.test(rawVal)) {
              bitVal = rawVal.charAt(0)
            } else {
              const padded = rawVal.padStart(sig.width, '0')
              const charIdx = sig.width - 1 - bit
              bitVal = padded.charAt(charIdx) || '0'
            }
            return { time: ev.time, value: bitVal }
          })

          result.push({
            fullName: `${sig.fullName}[${bit}]`,
            name: `${sig.name}[${bit}]`,
            scope: sig.scope,
            width: 1,
            range: '',
            isBus: false,
            isSubBit: true,
            parentBus: sig.name,
            events: bitEvents
          })
        }
      }
    })
    return result
  }

  // 1. Golden Wave (Input) signals
  const goldenInputSignals = useMemo(() => {
    const source = goldenParsed?.signals?.length ? goldenParsed : yourParsed
    if (!source) return []
    const raw = source.signals.filter(s => !isSignalOutput(s, ports))
    // Natural clock & reset first
    raw.sort((a, b) => {
      const score = s => {
        const n = s.name.toLowerCase()
        if (n === 'clk' || n === 'clock') return 1
        if (n === 'rst' || n === 'reset' || n === 'rst_n') return 2
        return 3
      }
      return score(a) - score(b)
    })
    return expandSignals(raw)
  }, [goldenParsed, yourParsed, ports, filterQuery, expandedBuses])

  // 2. Golden Wave (Output) signals
  const goldenOutputSignals = useMemo(() => {
    const source = goldenParsed?.signals?.length ? goldenParsed : yourParsed
    if (!source) return []
    const raw = source.signals.filter(s => isSignalOutput(s, ports))
    return expandSignals(raw)
  }, [goldenParsed, yourParsed, ports, filterQuery, expandedBuses])

  // 4. Your Wave (Output) signals
  const yourOutputSignals = useMemo(() => {
    if (!yourParsed) return []
    const raw = yourParsed.signals.filter(s => isSignalOutput(s, ports))
    return expandSignals(raw)
  }, [yourParsed, ports, filterQuery, expandedBuses])

  // 3. Match or Not (Single Bit) Comparison Timeline Events
  const matchTimeline = useMemo(() => {
    // Generate comparison points across all discrete time events
    const timePointsSet = new Set([0, maxTime])
    
    // Add all event timestamps from output signals
    goldenOutputSignals.forEach(s => s.events.forEach(e => timePointsSet.add(e.time)))
    yourOutputSignals.forEach(s => s.events.forEach(e => timePointsSet.add(e.time)))
    cycleLogs.forEach(c => {
      if (c?.time_num !== undefined) timePointsSet.add(c.time_num)
    })

    const sortedTimes = Array.from(timePointsSet).sort((a, b) => a - b)
    const intervals = []

    sortedTimes.forEach((t, idx) => {
      let isMatch = true

      // Check against explicit cycle logs
      const cycleAtT = cycleLogs.find(c => c?.time_num === t)
      if (cycleAtT && cycleAtT.match === false) {
        isMatch = false
      }

      // Check actual signals divergence
      if (isMatch && goldenOutputSignals.length > 0 && yourOutputSignals.length > 0) {
        for (const gSig of goldenOutputSignals) {
          if (gSig.isSubBit) continue
          const ySig = yourOutputSignals.find(s => s.name === gSig.name)
          if (ySig) {
            const gVal = getValueAtTime(gSig.events, t)
            const yVal = getValueAtTime(ySig.events, t)
            if (/[xz]/i.test(yVal) && !/[xz]/i.test(gVal)) {
              isMatch = false
              break
            }
            if (gVal !== yVal && !/[xz]/i.test(gVal)) {
              isMatch = false
              break
            }
          }
        }
      }

      intervals.push({
        time: t,
        match: isMatch,
        value: isMatch ? '1' : '0'
      })
    })

    return intervals
  }, [goldenOutputSignals, yourOutputSignals, cycleLogs, maxTime])

  // Status of single-bit match at current cursor
  const cursorMatchStatus = useMemo(() => {
    if (cursorTime === null) {
      return verdict === 'ACCEPTED'
    }
    let currentMatch = true
    for (const ev of matchTimeline) {
      if (ev.time <= cursorTime) {
        currentMatch = ev.match
      } else {
        break
      }
    }
    return currentMatch
  }, [cursorTime, matchTimeline, verdict])

  // Dimensions & coordinate mapping
  const baseWidth = 920
  const width = Math.max(baseWidth * zoom, 600)
  const left = 200
  const right = 30
  const plotWidth = width - left - right
  const rowHeight = 38
  const headerHeight = 32

  const timeToX = t => left + (t / maxTime) * plotWidth
  const xToTime = x => {
    const raw = ((x - left) / plotWidth) * maxTime
    return Math.max(0, Math.min(maxTime, Math.round(raw)))
  }

  // Calculate layout coordinates for all 4 sections
  const sec1Top = 44
  const sec1Height = headerHeight + Math.max(1, goldenInputSignals.length) * rowHeight
  
  const sec2Top = sec1Top + sec1Height + 14
  const sec2Height = headerHeight + Math.max(1, goldenOutputSignals.length) * rowHeight

  const sec3Top = sec2Top + sec2Height + 14
  const sec3Height = headerHeight + 1 * 44 // Single-bit match track

  const sec4Top = sec3Top + sec3Height + 14
  const sec4Height = headerHeight + Math.max(1, yourOutputSignals.length) * rowHeight

  const totalSvgHeight = sec4Top + sec4Height + 42

  // Minimap click / scrub
  function handleMinimapClick(e) {
    if (!minimapRef.current) return
    const rect = minimapRef.current.getBoundingClientRect()
    const clickX = e.clientX - rect.left
    const frac = Math.max(0, Math.min(1, clickX / rect.width))
    const clickedTime = Math.round(frac * maxTime)
    setCursorTime(clickedTime)

    const targetX = timeToX(clickedTime)
    if (scrollerRef.current) {
      scrollerRef.current.scrollLeft = targetX - scrollerRef.current.clientWidth / 2
    }
  }

  // Jump to first divergence
  function handleJumpToDivergence() {
    if (firstDivergenceTime === null) return
    setCursorTime(firstDivergenceTime)
    const targetX = timeToX(firstDivergenceTime)
    if (scrollerRef.current) {
      scrollerRef.current.scrollLeft = targetX - scrollerRef.current.clientWidth / 2
    }
  }

  function toggleBusExpansion(fullName) {
    setExpandedBuses(prev => ({
      ...prev,
      [fullName]: !prev[fullName]
    }))
  }

  function toggleAllBuses(expand) {
    const next = {}
    const all = [...goldenInputSignals, ...goldenOutputSignals, ...yourOutputSignals]
    all.forEach(s => {
      if (s.isBus) next[s.fullName] = expand
    })
    setExpandedBuses(next)
  }

  const hasAnyExpanded = Object.values(expandedBuses).some(Boolean)

  if (!yourParsed && !goldenParsed) {
    return (
      <div className="wave-placeholder unified-empty-card">
        <div className="wave-icon pulse-glow">📈</div>
        <h3>No Simulation Waveform Yet</h3>
        <p>Run your HDL code to compile with Icarus Verilog and view the unified 4-section waveform viewer.</p>
        <div className="unified-section-preview-list">
          <span className="p-tag">1. Golden Wave (Input)</span>
          <span className="p-tag">2. Golden Wave (Output)</span>
          <span className="p-tag">3. Match or Not (Single Bit)</span>
          <span className="p-tag">4. Your Wave (Output)</span>
        </div>
      </div>
    )
  }

  return (
    <div className="wave-viewer-container unified-waveform-viewer-container">
      {/* Waveform Controls Header */}
      <div className="wave-controls-bar modern-unified-toolbar">
        <div className="wave-left-controls">
          <div className="unified-viewer-title-badge">
            <span className="viewer-brand-icon">📈</span>
            <span className="viewer-brand-name">UNIFIED WAVEFORM VIEWER</span>
            <span className="viewer-spec-tag">4-SECTION EDA</span>
          </div>

          {/* Signal Search */}
          <div className="wave-search-box compact">
            <span className="search-glyph">🔍</span>
            <input
              type="text"
              className="wave-search-input"
              placeholder="Filter signals..."
              value={filterQuery}
              onChange={e => setFilterQuery(e.target.value)}
            />
          </div>

          {/* Expand/Collapse Buses */}
          <button
            type="button"
            className="filter-pill bus-toggle-pill"
            onClick={() => toggleAllBuses(!hasAnyExpanded)}
          >
            {hasAnyExpanded ? '[-] Collapse Buses' : '[+] Expand Buses'}
          </button>
        </div>

        {/* Right Actions */}
        <div className="wave-right-controls">
          {/* Time & Cursor Info */}
          <div className="time-badge unified-time-badge">
            <span>0 - {maxTime}{timescale}</span>
            {cursorTime !== null && (
              <span className="cursor-tag glow-amber">
                Cursor: <strong>{cursorTime}{timescale}</strong>
              </span>
            )}
          </div>

          {/* Jump to First Divergence */}
          {firstDivergenceTime !== null && (
            <button
              type="button"
              className="jump-fail-btn pulse-red"
              onClick={handleJumpToDivergence}
              title="Move cursor to first divergence between Golden and Your wave"
            >
              🚨 Jump to Divergence ({firstDivergenceTime}ns)
            </button>
          )}

          {/* Radix Selector */}
          <div className="radix-group compact-radix">
            <span className="group-label">Radix:</span>
            {['hex', 'dec', 'bin', 'ascii'].map(r => (
              <button
                key={r}
                type="button"
                className={`radix-btn ${radix === r ? 'active' : ''}`}
                onClick={() => setRadix(r)}
              >
                {r.toUpperCase()}
              </button>
            ))}
          </div>

          {/* Zoom Controls */}
          <div className="zoom-group compact-zoom">
            <button type="button" className="zoom-btn" onClick={() => setZoom(z => Math.min(z * 1.3, 4.0))}>+</button>
            <button type="button" className="zoom-btn" onClick={() => setZoom(z => Math.max(z / 1.3, 0.4))}>-</button>
            <button type="button" className="zoom-btn reset" onClick={() => setZoom(1.0)}>Fit</button>
          </div>
        </div>
      </div>

      {/* Global Synchronized Minimap Timeline */}
      {showMinimap && (
        <div
          className="wave-minimap-container"
          ref={minimapRef}
          onClick={handleMinimapClick}
          title="Scrub timeline to synchronize cursor across all 4 sections"
        >
          <div className="minimap-header-label">
            <span>SYNCHRONIZED TIMELINE (0ns — {maxTime}{timescale})</span>
            <span className="minimap-hint">Click or scrub to navigate all 4 sections</span>
          </div>

          <svg viewBox="0 0 1000 36" preserveAspectRatio="none" className="minimap-svg">
            {[0, 250, 500, 750, 1000].map(gx => (
              <g key={`mgrid-${gx}`}>
                <line x1={gx} y1="0" x2={gx} y2="36" stroke="#1e293b" strokeDasharray="2 2" />
                <text x={gx + 4} y="32" fill="#64748b" fontSize="9" fontFamily="'DM Mono', monospace">
                  {Math.round((gx / 1000) * maxTime)}ns
                </text>
              </g>
            ))}

            {/* Test Scenario Markers */}
            {testResults.map((t, idx) => {
              if (t.time_ns === undefined) return null
              const mx = (t.time_ns / maxTime) * 1000
              const isPass = t.status === 'PASSED'
              return (
                <g key={`test-pin-${idx}`}>
                  <line x1={mx} y1="2" x2={mx} y2="34" stroke={isPass ? '#10b981' : '#ef4444'} strokeWidth="1.5" />
                  <circle cx={mx} cy="8" r="3.5" fill={isPass ? '#10b981' : '#ef4444'} />
                </g>
              )
            })}

            {/* Cursor Guideline */}
            {cursorTime !== null && (
              <line
                x1={(cursorTime / maxTime) * 1000}
                y1="0"
                x2={(cursorTime / maxTime) * 1000}
                y2="36"
                stroke="#f59e0b"
                strokeWidth="2"
              />
            )}

            {/* Divergence Guideline */}
            {firstDivergenceTime !== null && (
              <line
                x1={(firstDivergenceTime / maxTime) * 1000}
                y1="0"
                x2={(firstDivergenceTime / maxTime) * 1000}
                y2="36"
                stroke="#ef4444"
                strokeWidth="2.5"
                strokeDasharray="3 2"
              />
            )}
          </svg>
        </div>
      )}

      {/* ONE UNIFIED WAVEFORM VIEWER (All 4 Sections Inside Same Container) */}
      <div className="unified-waveform-viewport" ref={scrollerRef}>
        <svg
          viewBox={`0 0 ${width} ${totalSvgHeight}`}
          className="unified-wave-svg"
          onMouseMove={e => {
            const rect = e.currentTarget.getBoundingClientRect()
            const scale = width / rect.width
            const svgX = (e.clientX - rect.left) * scale
            if (svgX >= left && svgX <= width - right) {
              setCursorTime(xToTime(svgX))
            }
          }}
        >
          {/* Defs for gradients & patterns */}
          <defs>
            <linearGradient id="matchGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.05" />
            </linearGradient>
            <linearGradient id="mismatchGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0.10" />
            </linearGradient>
          </defs>

          {/* Global Time Grid Lines through all 4 sections */}
          {Array.from({ length: 9 }, (_, i) => {
            const frac = i / 8
            const t = Math.round(maxTime * frac)
            const gx = timeToX(t)
            return (
              <g key={`unified-grid-${i}`}>
                <line x1={gx} y1={24} x2={gx} y2={totalSvgHeight - 20} stroke="#1e293b" strokeDasharray="2 3" strokeWidth="1" />
                <text x={gx} y={18} textAnchor="middle" fill="#64748b" fontSize="10" fontFamily="'DM Mono', monospace">
                  {t}ns
                </text>
                <text x={gx} y={totalSvgHeight - 6} textAnchor="middle" fill="#64748b" fontSize="10" fontFamily="'DM Mono', monospace">
                  {t}ns
                </text>
              </g>
            )
          })}

          {/* Cursor Guideline Across All 4 Sections */}
          {cursorTime !== null && (
            <g className="cursor-unified-line-group">
              <line
                x1={timeToX(cursorTime)}
                y1={12}
                x2={timeToX(cursorTime)}
                y2={totalSvgHeight - 16}
                stroke="#fbbf24"
                strokeWidth="1.8"
                strokeDasharray="4 2"
              />
              <rect
                x={timeToX(cursorTime) - 24}
                y={6}
                width="48"
                height="16"
                rx="3"
                fill="#451a03"
                stroke="#f59e0b"
                strokeWidth="1"
              />
              <text
                x={timeToX(cursorTime)}
                y={18}
                textAnchor="middle"
                fill="#fde047"
                fontSize="9"
                fontFamily="'DM Mono', monospace"
                fontWeight="800"
              >
                {cursorTime}ns
              </text>
            </g>
          )}

          {/* First Divergence Marker Across All Sections */}
          {firstDivergenceTime !== null && (
            <g className="divergence-unified-marker">
              <line
                x1={timeToX(firstDivergenceTime)}
                y1={12}
                x2={timeToX(firstDivergenceTime)}
                y2={totalSvgHeight - 16}
                stroke="#ef4444"
                strokeWidth="2"
                strokeDasharray="4 2"
              />
            </g>
          )}

          {/* ============================================================== */}
          {/* SECTION 1: Golden Wave (Input)                                 */}
          {/* ============================================================== */}
          <g className="waveform-section-group section-golden-inputs">
            {/* Section Header Bar */}
            <rect x="0" y={sec1Top} width={width} height={headerHeight} fill="#0d1829" stroke="#1e3a5f" strokeWidth="1" />
            <rect x="0" y={sec1Top} width="4" height={headerHeight} fill="#38bdf8" />
            <text x="14" y={sec1Top + 20} fill="#38bdf8" fontSize="12" fontWeight="700" fontFamily="system-ui, sans-serif">
              1. Golden Wave (Input)
            </text>
            <text x="175" y={sec1Top + 20} fill="#64748b" fontSize="10.5" fontFamily="system-ui, sans-serif">
              [Input waveform visualization — Stimuli & Clocks]
            </text>

            {/* Signals in Section 1 */}
            {goldenInputSignals.map((sig, row) => {
              const y = sec1Top + headerHeight + row * rowHeight
              return renderSignalRow(sig, y, '#38bdf8', '#38bdf8', false)
            })}
          </g>

          {/* ============================================================== */}
          {/* SECTION 2: Golden Wave (Output)                                */}
          {/* ============================================================== */}
          <g className="waveform-section-group section-golden-outputs">
            {/* Section Header Bar */}
            <rect x="0" y={sec2Top} width={width} height={headerHeight} fill="#06281e" stroke="#064e3b" strokeWidth="1" />
            <rect x="0" y={sec2Top} width="4" height={headerHeight} fill="#10b981" />
            <text x="14" y={sec2Top + 20} fill="#10b981" fontSize="12" fontWeight="700" fontFamily="system-ui, sans-serif">
              2. Golden Wave (Output)
            </text>
            <text x="185" y={sec2Top + 20} fill="#64748b" fontSize="10.5" fontFamily="system-ui, sans-serif">
              [Expected output waveform — Reference Design]
            </text>

            {/* Signals in Section 2 */}
            {goldenOutputSignals.map((sig, row) => {
              const y = sec2Top + headerHeight + row * rowHeight
              return renderSignalRow(sig, y, '#10b981', '#10b981', false)
            })}
          </g>

          {/* ============================================================== */}
          {/* SECTION 3: Match or Not (Single Bit)                           */}
          {/* ============================================================== */}
          <g className="waveform-section-group section-match-single-bit">
            {/* Section Header Bar */}
            <rect
              x="0"
              y={sec3Top}
              width={width}
              height={headerHeight}
              fill={cursorMatchStatus ? "#062b1e" : "#2b0a0a"}
              stroke={cursorMatchStatus ? "#059669" : "#dc2626"}
              strokeWidth="1"
            />
            <rect x="0" y={sec3Top} width="4" height={headerHeight} fill={cursorMatchStatus ? "#10b981" : "#ef4444"} />
            <text
              x="14"
              y={sec3Top + 20}
              fill={cursorMatchStatus ? "#34d399" : "#f87171"}
              fontSize="12"
              fontWeight="700"
              fontFamily="system-ui, sans-serif"
            >
              3. Match or Not (Single Bit)
            </text>
            <text x="210" y={sec3Top + 20} fill="#94a3b8" fontSize="10.5" fontFamily="system-ui, sans-serif">
              [Single-bit comparison: MATCH / MISMATCH]
            </text>

            {/* Instantaneous Match / Mismatch Pill in Section Header */}
            <g transform={`translate(${width - right - 130}, ${sec3Top + 6})`}>
              <rect
                x="0"
                y="0"
                width="120"
                height="20"
                rx="10"
                fill={cursorMatchStatus ? "#064e3b" : "#7f1d1d"}
                stroke={cursorMatchStatus ? "#10b981" : "#ef4444"}
                strokeWidth="1.2"
              />
              <text
                x="60"
                y="14"
                textAnchor="middle"
                fill={cursorMatchStatus ? "#a7f3d0" : "#fecaca"}
                fontSize="10"
                fontWeight="800"
                fontFamily="'DM Mono', monospace"
              >
                {cursorMatchStatus ? '✓ MATCH (Bit 1)' : '✗ MISMATCH (Bit 0)'}
              </text>
            </g>

            {/* Single-Bit Match Track Canvas */}
            {(() => {
              const y = sec3Top + headerHeight
              const trackH = 44
              const topY = y + 6
              const botY = y + 32

              return (
                <g className="single-bit-match-track">
                  {/* Left Label */}
                  <rect x="0" y={y} width={left} height={trackH} fill="#0b1324" />
                  <text x="14" y={y + 19} fill="#f1f5f9" fontSize="11" fontWeight="700" fontFamily="'DM Mono', monospace">
                    MATCH_STATUS
                  </text>
                  <text x="14" y={y + 33} fill="#64748b" fontSize="9" fontFamily="'DM Mono', monospace">
                    1-bit comparator
                  </text>

                  {/* Instantaneous value at cursor */}
                  <text
                    x={left - 12}
                    y={y + 25}
                    textAnchor="end"
                    fill={cursorMatchStatus ? '#10b981' : '#ef4444'}
                    fontSize="11.5"
                    fontFamily="'DM Mono', monospace"
                    fontWeight="800"
                  >
                    {cursorMatchStatus ? '1 (MATCH)' : '0 (MISMATCH)'}
                  </text>

                  {/* Baseline Line */}
                  <line x1={left} y1={botY} x2={width - right} y2={botY} stroke="#1e293b" />

                  {/* Single-Bit Step Waveform and Filled Match / Mismatch Polygons */}
                  {matchTimeline.map((ev, i) => {
                    const next = matchTimeline[i + 1]
                    const x1 = timeToX(ev.time)
                    const x2 = next ? timeToX(next.time) : timeToX(maxTime)
                    if (x2 - x1 < 1) return null

                    const isMatch = ev.match
                    const waveY = isMatch ? topY : botY

                    return (
                      <g key={`match-step-${i}`}>
                        {/* Shaded Area */}
                        <rect
                          x={x1}
                          y={topY}
                          width={x2 - x1}
                          height={botY - topY}
                          fill={isMatch ? "url(#matchGrad)" : "url(#mismatchGrad)"}
                        />
                        {/* Digital Signal Top / Low Edge */}
                        <line
                          x1={x1}
                          y1={waveY}
                          x2={x2}
                          y2={waveY}
                          stroke={isMatch ? "#10b981" : "#ef4444"}
                          strokeWidth="2.4"
                        />
                        {/* Vertical transition edge to next */}
                        {next && next.match !== ev.match && (
                          <line
                            x1={x2}
                            y1={topY}
                            x2={x2}
                            y2={botY}
                            stroke={next.match ? "#10b981" : "#ef4444"}
                            strokeWidth="2.4"
                          />
                        )}
                        {/* Text annotation for intervals */}
                        {x2 - x1 > 42 && (
                          <text
                            x={(x1 + x2) / 2}
                            y={y + 22}
                            textAnchor="middle"
                            fill={isMatch ? "#a7f3d0" : "#fca5a5"}
                            fontSize="9"
                            fontFamily="'DM Mono', monospace"
                            fontWeight="800"
                          >
                            {isMatch ? 'MATCH' : 'MISMATCH'}
                          </text>
                        )}
                      </g>
                    )
                  })}
                </g>
              )
            })()}
          </g>

          {/* ============================================================== */}
          {/* SECTION 4: Your Wave (Output)                                  */}
          {/* ============================================================== */}
          <g className="waveform-section-group section-your-outputs">
            {/* Section Header Bar */}
            <rect x="0" y={sec4Top} width={width} height={headerHeight} fill="#141c2e" stroke="#1e3a5f" strokeWidth="1" />
            <rect x="0" y={sec4Top} width="4" height={headerHeight} fill="#00f2fe" />
            <text x="14" y={sec4Top + 20} fill="#00f2fe" fontSize="12" fontWeight="700" fontFamily="system-ui, sans-serif">
              4. Your Wave (Output)
            </text>
            <text x="175" y={sec4Top + 20} fill="#64748b" fontSize="10.5" fontFamily="system-ui, sans-serif">
              [Actual output waveform — User Submitted RTL]
            </text>

            {/* Signals in Section 4 */}
            {yourOutputSignals.map((sig, row) => {
              const y = sec4Top + headerHeight + row * rowHeight
              return renderSignalRow(sig, y, '#00f2fe', '#00f2fe', true)
            })}
          </g>
        </svg>
      </div>

      {/* Unified Legend Footer */}
      <div className="wave-footer-legend modern-unified-footer">
        <span className="legend-tag"><span className="dot blue-dot" /> Golden Input (Blue)</span>
        <span className="legend-tag"><span className="dot green-dot" /> Golden Expected Output (Green)</span>
        <span className="legend-tag"><span className="dot cyan-dot" /> Your Actual Output (Cyan)</span>
        <span className="legend-tag"><span className="dot match-green-dot" /> Match (Green)</span>
        <span className="legend-tag"><span className="dot mismatch-red-dot" /> Mismatch (Red)</span>
        <span className="legend-tip">
          💡 Unified 4-section EDA viewer keeps all input, output, and single-bit comparator waveforms in lockstep.
        </span>
      </div>
    </div>
  )

  /**
   * Helper to render a single signal row inside the unified SVG
   */
  function renderSignalRow(sig, y, strokeColor, fillColor, isYourTrace) {
    const sortedEvents = [...sig.events].sort((a, b) => a.time - b.time)
    if (sortedEvents.length === 0 || sortedEvents[0].time > 0) {
      sortedEvents.unshift({ time: 0, value: sortedEvents[0]?.value || 'x' })
    }

    const valAtCursor = cursorTime !== null ? getValueAtTime(sortedEvents, cursorTime) : null
    const isSubBit = Boolean(sig.isSubBit)
    const isBus = sig.isBus
    const isExpanded = Boolean(expandedBuses[sig.fullName])

    // Detect divergence from comparator
    let isDivergent = false
    if (isYourTrace && cursorTime !== null && valAtCursor !== null) {
      const gSig = goldenOutputSignals.find(s => s.name === sig.name)
      if (gSig) {
        const gVal = getValueAtTime(gSig.events, cursorTime)
        if (gVal !== valAtCursor && !/[xz]/i.test(gVal)) {
          isDivergent = true
        }
      }
    }

    return (
      <g key={`${sig.fullName}_${y}`} className={`signal-row-group ${isSubBit ? 'sub-bit-row' : ''}`}>
        {/* Signal Background in Label Area */}
        <rect x="0" y={y} width={left} height={rowHeight} fill={isSubBit ? "#090f1d" : "#0d1526"} />

        {/* Expand / Collapse Icon for Buses */}
        {isBus && (
          <text
            x="8"
            y={y + 22}
            fill="#38bdf8"
            fontSize="11"
            fontWeight="700"
            style={{ cursor: 'pointer', userSelect: 'none' }}
            onClick={() => toggleBusExpansion(sig.fullName)}
            title={isExpanded ? "Collapse bus" : "Expand bus into individual wires"}
          >
            {isExpanded ? '▼' : '▶'}
          </text>
        )}

        {/* Sub-bit connector */}
        {isSubBit && (
          <path d={`M 14 ${y} L 14 ${y + 18} L 22 ${y + 18}`} fill="none" stroke="#334155" strokeWidth="1" />
        )}

        {/* Signal Name */}
        <text
          x={isSubBit ? "26" : (isBus ? "24" : "12")}
          y={y + 21}
          fill={isSubBit ? "#94a3b8" : "#e2e8f0"}
          fontSize={isSubBit ? "10.5" : "11.5"}
          fontWeight={isSubBit ? "500" : "600"}
          fontFamily="'DM Mono', monospace"
        >
          {sig.name}
          {sig.range ? <tspan fill="#60a5fa" fontSize="9.5"> {sig.range}</tspan> : ''}
        </text>

        {/* Instantaneous Value at Cursor */}
        {valAtCursor !== null && (
          <text
            x={left - 10}
            y={y + 21}
            textAnchor="end"
            fill={isDivergent ? "#ef4444" : (/[xz]/i.test(valAtCursor) ? "#f59e0b" : strokeColor)}
            fontSize="11"
            fontFamily="'DM Mono', monospace"
            fontWeight="700"
          >
            {formatValue(valAtCursor, isBus)}
          </text>
        )}

        {/* Track Baseline */}
        <line x1={left} y1={y + 32} x2={width - right} y2={y + 32} stroke="#172238" />

        {/* Bus Hexagonal Trace vs Scalar Square Wave */}
        {isBus ? (
          sortedEvents.map((ev, i) => {
            const next = sortedEvents[i + 1]
            const x1 = timeToX(ev.time)
            const x2 = next ? timeToX(next.time) : timeToX(maxTime)
            if (x2 - x1 < 1.5) return null

            const hTop = y + 4
            const hMid = y + 17
            const hBot = y + 30
            const slant = Math.min(4, (x2 - x1) / 3)

            const points = [
              `${x1},${hMid}`,
              `${x1 + slant},${hTop}`,
              `${x2 - slant},${hTop}`,
              `${x2},${hMid}`,
              `${x2 - slant},${hBot}`,
              `${x1 + slant},${hBot}`
            ].join(' ')

            const isUnknown = /[xz]/i.test(ev.value)
            const textVal = formatValue(ev.value, true)

            return (
              <g key={`bus-${ev.time}-${i}`}>
                <polygon
                  points={points}
                  fill={isUnknown ? '#3b1d11' : (isYourTrace ? '#0c1f38' : '#072e23')}
                  stroke={isUnknown ? '#f59e0b' : strokeColor}
                  strokeWidth="1.4"
                />
                {x2 - x1 > 32 && (
                  <text
                    x={(x1 + x2) / 2}
                    y={hMid + 4}
                    textAnchor="middle"
                    fill={isUnknown ? '#fbbf24' : '#f8fafc'}
                    fontSize="9.5"
                    fontFamily="'DM Mono', monospace"
                    fontWeight="600"
                  >
                    {textVal}
                  </text>
                )}
              </g>
            )
          })
        ) : (
          <path
            d={(() => {
              const getLevel = val => {
                if (val === '1') return y + 4
                if (val === '0') return y + 30
                return y + 17
              }
              let d = `M ${timeToX(sortedEvents[0].time)} ${getLevel(sortedEvents[0].value)}`
              sortedEvents.forEach((ev, idx) => {
                if (idx === 0) return
                d += ` H ${timeToX(ev.time)}`
                d += ` V ${getLevel(ev.value)}`
              })
              d += ` H ${timeToX(maxTime)}`
              return d
            })()}
            fill="none"
            stroke={isDivergent ? "#ef4444" : (isSubBit ? "#38bdf8" : strokeColor)}
            strokeWidth={isSubBit ? "1.4" : "1.8"}
          />
        )}
      </g>
    )
  }
}
