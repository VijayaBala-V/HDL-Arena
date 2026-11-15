import React from 'react'

export default function DebugAdvisor({ diagnostics, onJumpToWaveform }) {
  if (!diagnostics) {
    return (
      <div className="debug-empty neon-card">
        <div className="advisor-icon pulse-glow">🔍</div>
        <h3 className="neon-text-cyan">RTL Debug Advisor</h3>
        <p>Run a simulation to generate automated failure analysis, correlation with Golden Wave, and evidence-backed root-cause suggestions.</p>
      </div>
    )
  }

  const isAccepted = diagnostics.status === 'ACCEPTED'
  const evidence = diagnostics.evidence || []
  const causes = diagnostics.suspected_root_causes || []
  const recommendations = diagnostics.recommendations || []
  const failedScenarios = diagnostics.failed_scenarios || []
  const firstMismatch = diagnostics.first_mismatch || null
  const failureTime = diagnostics.failure_time_ns

  return (
    <div className="debug-advisor-panel neon-debug">
      {/* Header Status */}
      <div className={`advisor-status-banner ${isAccepted ? 'status-ok' : 'status-fail'}`}>
        <div className="status-icon">{isAccepted ? '✅' : '🔬'}</div>
        <div className="status-content">
          <h4>{isAccepted ? 'Verification Passed — Clean RTL Implementation' : 'RTL Diagnostic & Waveform Failure Analysis'}</h4>
          <p>
            {isAccepted
              ? 'All timing and assertion tests completed with zero detected hazards, unknown X-states, or latch inferences.'
              : `${failedScenarios.length} failing test scenario(s) detected. Correlating simulation evidence against expected behavior.`}
          </p>
        </div>
      </div>

      {/* Disclosed Mismatch Snapshot connected to Waveforms */}
      {firstMismatch && (
        <div className="failure-snapshot-card neon-box">
          <div className="snap-header">
            <span className="snap-title">⚠️ First Mismatched Assertion Snapshot</span>
            {failureTime !== null && (
              <span className="snap-time">Divergence Time: <strong>{failureTime} ns</strong></span>
            )}
          </div>
          <div className="snap-grid">
            <div className="snap-item">
              <span className="snap-label">Failed Scenario:</span>
              <span className="snap-val scenario-name">
                {failedScenarios[0]?.name || diagnostics.failed_test_id || 'Scenario Assertion'}
              </span>
            </div>
            <div className="snap-item">
              <span className="snap-label">Stimuli Inputs:</span>
              <code className="snap-val stimuli">{firstMismatch.inputs || '-'}</code>
            </div>
            <div className="snap-item">
              <span className="snap-label">Expected (Golden):</span>
              <code className="snap-val exp">{firstMismatch.expected || '-'}</code>
            </div>
            <div className="snap-item">
              <span className="snap-label">Actual (Your DUT):</span>
              <code className="snap-val act">{firstMismatch.actual || '-'}</code>
            </div>
          </div>

          {onJumpToWaveform && failureTime !== null && (
            <div className="snap-jump-row">
              <button
                className="cta-wave-btn pulse-glow"
                onClick={() => onJumpToWaveform(failureTime)}
                title="Synchronize Golden Wave and Your Wave cursors to this exact mismatch time"
              >
                📈 Snap Both Waveforms to Mismatch ({failureTime}ns) ➔
              </button>
            </div>
          )}
        </div>
      )}

      {/* Grid: Measured Observations vs Suspected Root Causes */}
      <div className="advisor-grid">
        {/* 1. Measured Evidence & Observations */}
        <div className="advisor-card">
          <div className="card-head">
            <span className="card-icon">📊</span>
            <h5>Measured Simulation Observations</h5>
          </div>
          {evidence.length === 0 ? (
            <p className="no-items">No signal timing anomalies or compilation warnings detected.</p>
          ) : (
            <ul className="evidence-list">
              {evidence.map((ev, i) => (
                <li key={i} className="evidence-item">
                  <span className="badge-measured">OBSERVED</span>
                  <span>{ev}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* 2. Suspected Root Causes & Behavioral Hypotheses */}
        <div className="advisor-card">
          <div className="card-head">
            <span className="card-icon">💡</span>
            <h5>Suspected RTL Root Causes</h5>
          </div>
          {causes.length === 0 ? (
            <p className="no-items">No design rule violations or hazard patterns detected.</p>
          ) : (
            <div className="causes-list">
              {causes.map((c, i) => (
                <div key={i} className="cause-item">
                  <span className="badge-hypothesis">HYPOTHESIS #{i + 1}</span>
                  <p>{c}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 3. Actionable Fixes & Best Practices */}
        <div className="advisor-card full-width">
          <div className="card-head">
            <span className="card-icon">🛠️</span>
            <h5>Recommended RTL Fixes & Design Best Practices</h5>
          </div>
          {recommendations.length === 0 ? (
            <p className="no-items">Your design follows good synchronous digital design practices.</p>
          ) : (
            <div className="recs-grid">
              {recommendations.map((rec, i) => (
                <div key={i} className="rec-box">
                  <span className="step-num">{i + 1}</span>
                  <p>{rec}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
