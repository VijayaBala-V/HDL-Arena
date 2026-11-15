import React, { useState } from 'react'
import VJCoinIcon from './VJCoinIcon'

export default function SpecPanel({
  problem,
  history = [],
  isBookmarked = false,
  onToggleBookmark,
  onRestoreSnapshot,
  onScrollToEditor,
  isUnlocked = false,
  solution = null,
  userCoins = 0,
  currentUserCode = {},
  onUnlockSolution,
  onLoadSolutionCode
}) {
  const [activeTab, setActiveTab] = useState('spec') // 'spec' | 'ports' | 'history' | 'solution'
  const [copiedInterface, setCopiedInterface] = useState(false)
  const [copiedSolutionFile, setCopiedSolutionFile] = useState(null)
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [unlocking, setUnlocking] = useState(false)
  const [solutionViewMode, setSolutionViewMode] = useState('reference') // 'reference' | 'compare'
  const [selectedSolutionFile, setSelectedSolutionFile] = useState('')

  function handleCopyInterface() {
    if (problem?.interface && navigator.clipboard) {
      navigator.clipboard.writeText(problem.interface)
      setCopiedInterface(true)
      setTimeout(() => setCopiedInterface(false), 2000)
    }
  }

  function handleCopySolutionCode(fileName, code) {
    if (code && navigator.clipboard) {
      navigator.clipboard.writeText(code)
      setCopiedSolutionFile(fileName)
      setTimeout(() => setCopiedSolutionFile(null), 2000)
    }
  }

  function handleDownloadFile(fileName, code) {
    if (!code) return
    const blob = new Blob([code], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  async function handleConfirmUnlock() {
    if (!onUnlockSolution || unlocking) return
    setUnlocking(true)
    try {
      await onUnlockSolution(problem.id)
      setShowConfirmModal(false)
    } finally {
      setUnlocking(false)
    }
  }

  if (!problem) return null

  const canonicalFiles = solution?.canonical_code || {}
  const fileNames = Object.keys(canonicalFiles)
  const activeFileName = selectedSolutionFile || fileNames[0] || ''
  const activeFileCode = canonicalFiles[activeFileName] || ''
  const userFileCode = currentUserCode?.[activeFileName] || Object.values(currentUserCode || {})[0] || '// Your code'

  const canAfford = userCoins >= 1

  return (
    <section id="problem-description-section" className="spec-section-full">
      {/* Confirmation Modal Before Spending 1 VJ Coin */}
      {showConfirmModal && (
        <div className="modal-overlay" onClick={() => !unlocking && setShowConfirmModal(false)}>
          <div className="modal-card unlock-confirm-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-row">
                <span className="modal-title-icon"><VJCoinIcon size={24} /></span>
                <div>
                  <h3>Unlock Reference Solution</h3>
                  <p className="modal-sub">Confirm 1 VJ Coin transaction</p>
                </div>
              </div>
              <button
                className="modal-close-btn"
                onClick={() => !unlocking && setShowConfirmModal(false)}
                disabled={unlocking}
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              <p className="confirm-prompt-text">
                Are you sure you want to spend <strong>1 VJ Coin</strong> to permanently unlock the official reference RTL implementation and design explanation for:
              </p>
              <div className="confirm-problem-chip">
                <strong>{problem.title}</strong> ({problem.id})
              </div>

              <div className="confirm-balance-row">
                <div className="bal-item">
                  <span>Current Balance:</span>
                  <strong><VJCoinIcon size={16} /> {userCoins} {userCoins === 1 ? 'VJ Coin' : 'VJ Coins'}</strong>
                </div>
                <div className="bal-arrow">➔</div>
                <div className="bal-item">
                  <span>After Unlock:</span>
                  <strong className="after-cost"><VJCoinIcon size={16} /> {Math.max(0, userCoins - 1)} {Math.max(0, userCoins - 1) === 1 ? 'VJ Coin' : 'VJ Coins'}</strong>
                </div>
              </div>

              <p className="confirm-policy-note">
                💡 <em>Once unlocked, this reference solution will remain accessible to your account permanently without additional cost.</em>
              </p>
            </div>

            <div className="modal-footer">
              <button
                className="cancel-btn"
                onClick={() => setShowConfirmModal(false)}
                disabled={unlocking}
              >
                Cancel
              </button>
              <button
                className="confirm-unlock-btn"
                onClick={handleConfirmUnlock}
                disabled={unlocking}
              >
                {unlocking ? 'Processing Transaction...' : 'Confirm & Unlock · 1 VJ Coin'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Top Banner / Meta Header */}
      <div className="spec-full-header">
        <div className="spec-meta-left">
          <div className="meta-tag-row">
            <span className={`diff-pill ${problem.difficulty?.toLowerCase()}`}>
              {problem.difficulty}
              {problem.difficulty === 'Medium' && ' (+1 VJ Coin on first solve)'}
              {problem.difficulty === 'Hard' && ' (+1 VJ Coin on first solve)'}
              {problem.difficulty === 'Easy' && ' (0 VJ Coins)'}
            </span>
            <span className="cat-pill">{problem.category}</span>
            {problem.tags?.map(t => (
              <span key={t} className="topic-tag">#{t}</span>
            ))}
            <button
              className={`spec-star-btn ${isBookmarked ? 'active' : ''}`}
              onClick={() => onToggleBookmark(problem.id)}
              title={isBookmarked ? 'Remove bookmark' : 'Bookmark problem'}
            >
              {isBookmarked ? '★ Bookmarked' : '☆ Bookmark'}
            </button>
          </div>

          <h2 className="spec-problem-title">
            {problem.title} <span className="problem-id-tag">({problem.id})</span>
          </h2>
          <div className="module-name-chip">
            <span>Top Module: </span>
            <code>{problem.module_name}</code>
          </div>
        </div>

        {/* Right Actions */}
        <div className="spec-header-right-actions">
          {onScrollToEditor && (
            <button
              className="back-to-code-btn"
              onClick={onScrollToEditor}
              title="Scroll back up to the code editor"
            >
              ⬆ Back to Editor
            </button>
          )}
        </div>
      </div>

      {/* Tabs Header: Description | Port Specs | History | Solution */}
      <div className="spec-full-tabs">
        <button
          className={`spec-full-tab-btn ${activeTab === 'spec' ? 'active' : ''}`}
          onClick={() => setActiveTab('spec')}
        >
          📖 Problem Statement & Requirements
        </button>
        <button
          className={`spec-full-tab-btn ${activeTab === 'ports' ? 'active' : ''}`}
          onClick={() => setActiveTab('ports')}
        >
          🔌 Port Specifications ({problem.ports?.length || 0})
        </button>
        <button
          className={`spec-full-tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          📜 Submission History ({history.length})
        </button>
        <button
          className={`spec-full-tab-btn solution-tab-pill ${activeTab === 'solution' ? 'active' : ''}`}
          onClick={() => setActiveTab('solution')}
        >
          {isUnlocked ? '💡 View Solution (Unlocked)' : '🔒 View Solution · 1 VJ Coin'}
        </button>
      </div>

      {/* Tab Content */}
      <div className="spec-full-body">
        {/* 1. Description Tab */}
        {activeTab === 'spec' && (
          <div className="spec-tab-content-block">
            {/* Problem Statement */}
            <div className="spec-content-card">
              <h3>Problem Statement</h3>
              <p className="description-text">{problem.description}</p>
            </div>

            {/* Functional Requirements */}
            {problem.requirements && problem.requirements.length > 0 && (
              <div className="spec-content-card">
                <h3>Functional Requirements & Timing</h3>
                <ul className="spec-req-list">
                  {problem.requirements.map((req, i) => (
                    <li key={i}>{req}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Design Constraints */}
            {problem.constraints && problem.constraints.length > 0 && (
              <div className="spec-content-card">
                <h3>Design Constraints & Operating Limits</h3>
                <ul className="spec-req-list">
                  {problem.constraints.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Canonical Port Interface */}
            {problem.interface && (
              <div className="spec-content-card">
                <div className="block-head-with-action">
                  <h3>Canonical Port Interface</h3>
                  <button className="copy-interface-btn" onClick={handleCopyInterface}>
                    {copiedInterface ? '✓ Copied!' : '📋 Copy Interface'}
                  </button>
                </div>
                <pre className="canonical-code-box">{problem.interface}</pre>
              </div>
            )}

            {/* RTL Synthesis Guidelines */}
            <div className="spec-content-card rtl-advice-card">
              <h4>💡 RTL Synthesis Guidelines</h4>
              <ul>
                <li>Use non-blocking assignments (<code>&lt;=</code>) exclusively for sequential registers updated on <code>posedge clk</code>.</li>
                <li>Avoid combinational loops and inferred latches by assigning all outputs in every branch of <code>always @(*)</code> blocks.</li>
                <li>Respect synchronous reset priority over functional increment or load conditions.</li>
              </ul>
            </div>
          </div>
        )}

        {/* 2. Ports Table Tab */}
        {activeTab === 'ports' && (
          <div className="spec-tab-content-block">
            <div className="spec-content-card">
              <h3>Hardware Port Specifications</h3>
              <p className="ports-sub">Signal definitions for top-level module <code>{problem.module_name}</code>:</p>
              {problem.ports && problem.ports.length > 0 ? (
                <div className="ports-table-wrapper">
                  <table className="ports-table">
                    <thead>
                      <tr>
                        <th>Signal</th>
                        <th>Direction</th>
                        <th>Width</th>
                        <th>Function & Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {problem.ports.map(pt => (
                        <tr key={pt.name}>
                          <td><code className="sig-name">{pt.name}</code></td>
                          <td>
                            <span className={`dir-tag ${pt.direction}`}>
                              {pt.direction.toUpperCase()}
                            </span>
                          </td>
                          <td className="width-col mono">{pt.width}</td>
                          <td className="desc-col">{pt.desc}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="empty-ports-notice" style={{ padding: '16px', color: '#8b949e', fontSize: '13px' }}>
                  ℹ️ This question format does not use hardware module port declarations. Evaluation is performed via programmatic execution, multiple-choice verification, or structured architectural rubric scoring.
                </div>
              )}
            </div>
          </div>
        )}

        {/* 3. Submissions History Tab */}
        {activeTab === 'history' && (
          <div className="spec-tab-content-block">
            <div className="spec-content-card">
              <h3>Past Submission Records</h3>
              {history.length === 0 ? (
                <p className="no-history-hint">No submissions recorded for this challenge yet. Press <strong>🚀 Submit</strong> to test your solution!</p>
              ) : (
                <div className="submissions-history-list">
                  {history.map(item => (
                    <div key={item.id} className="submission-card">
                      <div className="sub-top">
                        <span className={`verdict-badge ${item.verdict?.toLowerCase()}`}>
                          {item.verdict}
                        </span>
                        <span className="sub-time">{item.created_at || item.time}</span>
                      </div>
                      <div className="sub-bottom">
                        <span>{item.tests_passed !== undefined ? `${item.tests_passed}/${item.tests_total} tests passed` : item.message}</span>
                        {item.exec_time_ms ? <span className="time-metric">{item.exec_time_ms} ms</span> : null}
                      </div>
                      {item.code_snapshot && onRestoreSnapshot && (
                        <div className="sub-restore-row">
                          <button
                            className="restore-code-btn"
                            onClick={() => {
                              onRestoreSnapshot(item.code_snapshot)
                              if (onScrollToEditor) onScrollToEditor()
                            }}
                          >
                            ↺ Restore This Code Snapshot
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 4. Official Reference Solution Tab */}
        {activeTab === 'solution' && (
          <div className="spec-tab-content-block">
            {isUnlocked && solution ? (
              // Unlocked View
              <div className="solution-unlocked-container">
                <div className="solution-header-banner">
                  <div className="solution-badge-row">
                    <span className="unlocked-chip">✓ Solution Unlocked</span>
                    <span className="solution-title-chip">{solution.title}</span>
                  </div>
                  <h3>Design Architecture & Algorithm Explanation</h3>
                  <p className="solution-overview-text">{solution.overview}</p>
                </div>

                {/* Expected Timing & Corner Cases Cards */}
                <div className="solution-details-two-col">
                  {solution.timing_behavior && (
                    <div className="spec-content-card">
                      <h4>⏱️ Expected Timing & Protocol Behavior</h4>
                      <p className="text-content-sm">{solution.timing_behavior}</p>
                    </div>
                  )}

                  {solution.corner_cases && solution.corner_cases.length > 0 && (
                    <div className="spec-content-card">
                      <h4>⚠️ Critical Corner Cases Handled</h4>
                      <ul className="spec-req-list">
                        {solution.corner_cases.map((cc, i) => (
                          <li key={i}>{cc}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Hardware Synthesis & Resource Notes */}
                {solution.synthesis_notes && solution.synthesis_notes.length > 0 && (
                  <div className="spec-content-card synthesis-insights-card">
                    <h4>📐 Hardware Synthesis & Silicon Resource Considerations</h4>
                    <ul className="synthesis-notes-list">
                      {solution.synthesis_notes.map((note, idx) => (
                        <li key={idx}>
                          <span className="check-bullet">✓</span>
                          <span>{note}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Reference Code Viewer with Copy, Download & Side-by-Side Comparison */}
                <div className="spec-content-card canonical-solution-card">
                  <div className="canonical-card-top">
                    <div className="sol-card-title-col">
                      <h4>Reference RTL Implementation</h4>
                      <p className="sub-note">Tested and fully verified against 100% of hidden testbench assertions.</p>
                    </div>

                    <div className="solution-toolbar-actions">
                      {/* View Mode Toggle: Reference vs Comparison */}
                      <div className="view-mode-pill-toggle">
                        <button
                          className={`mode-btn ${solutionViewMode === 'reference' ? 'active' : ''}`}
                          onClick={() => setSolutionViewMode('reference')}
                        >
                          👁️ Solution Only
                        </button>
                        <button
                          className={`mode-btn ${solutionViewMode === 'compare' ? 'active' : ''}`}
                          onClick={() => setSolutionViewMode('compare')}
                        >
                          ⚖️ Compare with My Code
                        </button>
                      </div>

                      {/* File Tabs if multi-file */}
                      {fileNames.length > 1 && (
                        <div className="sol-file-tabs">
                          {fileNames.map(f => (
                            <button
                              key={f}
                              className={`sol-file-tab-btn ${f === activeFileName ? 'active' : ''}`}
                              onClick={() => setSelectedSolutionFile(f)}
                            >
                              📄 {f}
                            </button>
                          ))}
                        </div>
                      )}

                      <button
                        className="mini-action-btn"
                        onClick={() => handleCopySolutionCode(activeFileName, activeFileCode)}
                      >
                        {copiedSolutionFile === activeFileName ? '✓ Copied!' : '📋 Copy Solution'}
                      </button>

                      <button
                        className="mini-action-btn"
                        onClick={() => handleDownloadFile(activeFileName, activeFileCode)}
                      >
                        💾 Download {activeFileName}
                      </button>

                      {onLoadSolutionCode && (
                        <button
                          className="load-solution-btn"
                          onClick={() => {
                            onLoadSolutionCode(solution.canonical_code)
                            if (onScrollToEditor) onScrollToEditor()
                          }}
                          title="Copy reference code into your active editor workspace"
                        >
                          ⚡ Load into Editor
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Mode 1: Reference Only View */}
                  {solutionViewMode === 'reference' && (
                    <div className="canonical-file-block">
                      <div className="file-block-header">
                        <span className="fname-tag">📄 {activeFileName} (Read-Only Golden Reference)</span>
                      </div>
                      <pre className="canonical-code-display">{activeFileCode}</pre>
                    </div>
                  )}

                  {/* Mode 2: Side-by-Side / Comparison View */}
                  {solutionViewMode === 'compare' && (
                    <div className="compare-views-grid">
                      <div className="compare-pane user-pane">
                        <div className="pane-header">
                          <span>👤 Your Current Editor Code ({activeFileName})</span>
                        </div>
                        <pre className="canonical-code-display compare-pre">{userFileCode}</pre>
                      </div>

                      <div className="compare-pane reference-pane">
                        <div className="pane-header">
                          <span>⭐ Golden Reference Solution ({activeFileName})</span>
                        </div>
                        <pre className="canonical-code-display compare-pre">{activeFileCode}</pre>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              // Locked View
              <div className="solution-locked-card">
                <div className="lock-icon-badge">🔒</div>
                <h3>Reference Solution Locked</h3>
                <p className="lock-sub-message">
                  The verified reference RTL implementation, module architecture, timing behavior analysis, and corner case notes are protected.
                </p>

                <div className="unlock-conditions-grid">
                  <div className="cond-card">
                    <div className="cond-icon"><VJCoinIcon size={24} /></div>
                    <div className="cond-body">
                      <h5>Unlock Solution · 1 VJ Coin</h5>
                      <p>Spend 1 Virtual Judge Coin to unlock the complete golden RTL implementation and architecture notes permanently.</p>
                    </div>
                  </div>

                  <div className="cond-card">
                    <div className="cond-icon">⚡</div>
                    <div className="cond-body">
                      <h5>How to Earn VJ Coins</h5>
                      <p>Claim your <strong>1 VJ Coin</strong> daily login reward or solve Medium (+1 Coin) and Hard (+1 Coin) problems.</p>
                    </div>
                  </div>
                </div>

                <div className="unlock-action-footer">
                  <div className="user-coin-balance-pill">
                    <span>Available Balance:</span>
                    <strong><VJCoinIcon size={16} /> {userCoins} {userCoins === 1 ? 'VJ Coin' : 'VJ Coins'}</strong>
                  </div>

                  {canAfford ? (
                    <button
                      className="unlock-submit-btn affordable"
                      onClick={() => setShowConfirmModal(true)}
                    >
                      🔓 View Solution · 1 VJ Coin
                    </button>
                  ) : (
                    <div className="insufficient-funds-box">
                      <button className="unlock-submit-btn disabled" disabled>
                        Insufficient Coins (1 VJ Coin Required)
                      </button>
                      <p className="insufficient-msg">
                        ⚠️ You have 0 VJ Coins. Solve a Medium or Hard problem, or return tomorrow to collect your daily login coin!
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  )
}
