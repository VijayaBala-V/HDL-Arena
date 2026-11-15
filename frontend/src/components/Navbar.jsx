import React, { useState } from 'react'
import VJCoinIcon from './VJCoinIcon'
import AccountDropdown from './AccountDropdown'

export default function Navbar({
  currentView,
  onChangeView,
  problems,
  currentProblemId,
  onSelectProblem,
  backendOnline,
  onRunSample,
  onSubmitFull,
  loading,
  canRun,
  streak = 0,
  coins = null,
  coinLoading = false,
  coinError = null,
  onRetryCoins,
  animateCoins = false,
  claimedToday = false,
  username = '',
  currentUser = null,
  showToast = () => {},
  selectedIde = 'verilog',
  onSelectIde,
  language = 'verilog',
  onSelectLanguage,
  onOpenStreakModal,
  onClaimDailyReward,
  onOpenAuthModal,
  onScrollToDescription
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <header className="hdl-navbar">
      {/* Left: Brand & Nav Links */}
      <div className="nav-brand-section">
        <div
          className="brand-logo-btn"
          onClick={() => {
            onChangeView('workspace')
            setMobileMenuOpen(false)
          }}
          title="HDL Arena - Return to IDE Workspace"
        >
          <span className="logo-bolt">⚡</span>
          <span className="logo-text">HDL<span className="text-accent">Arena</span></span>
          <span className="logo-tag">PRO</span>
        </div>

        {/* Mobile Hamburger Button */}
        <button
          className={`mobile-menu-toggle-btn ${mobileMenuOpen ? 'open' : ''}`}
          onClick={() => setMobileMenuOpen(prev => !prev)}
          title="Toggle navigation menu"
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? '✕' : '☰'}
        </button>

        {/* Desktop / Collapsible Mobile Navigation Links */}
        <nav className={`nav-pages-links ${mobileMenuOpen ? 'mobile-open' : ''}`}>
          <button
            className={`nav-link-btn ${currentView === 'workspace' ? 'active' : ''}`}
            onClick={() => {
              onChangeView('workspace')
              setMobileMenuOpen(false)
            }}
          >
            💻 Workspace
          </button>
          <button
            className={`nav-link-btn ${currentView === 'problems' ? 'active' : ''}`}
            onClick={() => {
              onChangeView('problems')
              setMobileMenuOpen(false)
            }}
          >
            📚 Problems
          </button>
          <button
            className={`nav-link-btn ${currentView === 'tracks' ? 'active' : ''}`}
            onClick={() => {
              onChangeView('tracks')
              setMobileMenuOpen(false)
            }}
          >
            🗺️ Tracks
          </button>
          <button
            className={`nav-link-btn ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => {
              onChangeView('dashboard')
              setMobileMenuOpen(false)
            }}
          >
            👤 Dashboard
          </button>
        </nav>
      </div>

      {/* Middle: Challenge Selector & Jump to Description (When in Workspace) */}
      {currentView === 'workspace' && (
        <div className="nav-problem-selector">
          <span className="prob-label">CHALLENGE:</span>
          <select
            className="prob-dropdown"
            value={currentProblemId}
            onChange={e => onSelectProblem(e.target.value)}
            aria-label="Select digital logic problem"
          >
            {problems.map(p => (
              <option key={p.id} value={p.id}>
                {p.title} ({p.difficulty})
              </option>
            ))}
          </select>

          {onScrollToDescription && (
            <button
              className="nav-spec-jump-btn"
              onClick={onScrollToDescription}
              title="Jump down to Problem Statement and Port Specifications"
            >
              📖 Spec ↓
            </button>
          )}
        </div>
      )}

      {/* Right: Coins, Streak & Execution Controls */}
      <div className="nav-actions-section">
        {/* Daily streak indicator */}
        <button
          className="streak-badge-pill clickable"
          onClick={onOpenStreakModal}
          title="Daily practice streak (Asia/Kolkata calendar)"
        >
          <span>🔥 {streak > 0 ? `${streak}-day streak` : '0-day streak'}</span>
        </button>

        {/* Authoritative VJ Coin Balance Pill */}
        {coinLoading ? (
          <button
            className="coins-badge-pill loading-pill"
            title="Fetching VJ Coin balance from backend..."
            disabled
          >
            <VJCoinIcon size={18} animate={true} />
            <span className="coin-state-text">Fetching...</span>
          </button>
        ) : coinError ? (
          <button
            className="coins-badge-pill error-pill clickable"
            onClick={onRetryCoins}
            title={`${coinError} (Click to retry)`}
          >
            <VJCoinIcon size={18} />
            <span className="coin-err-badge">⚠️ Retry</span>
          </button>
        ) : (
          <button
            className={`coins-badge-pill clickable ${animateCoins ? 'bump-animate' : ''}`}
            onClick={onOpenStreakModal}
            title="VJ Coin Balance — Click to view Rewards Ledger & Unlock history"
          >
            <VJCoinIcon size={18} animate={animateCoins} />
            <span className="coin-amount-text">
              {coins !== null ? `${typeof coins === 'number' ? (Number.isInteger(coins) ? coins : coins.toFixed(1)) : coins} ${coins === 1 ? 'VJ Coin' : 'VJ Coins'}` : '—'}
            </span>
          </button>
        )}

        {/* Claim daily reward shortcut */}
        {onClaimDailyReward && (
          <button
            className={`nav-quick-claim-btn ${claimedToday ? 'claimed' : 'ready'}`}
            onClick={!claimedToday ? onClaimDailyReward : undefined}
            disabled={claimedToday}
            title={
              claimedToday
                ? '1 VJ Coin daily reward already claimed for today'
                : 'Claim your +1 VJ Coin daily login reward'
            }
          >
            {claimedToday ? '✓ Claimed Today' : '+1 VJ Coin'}
          </button>
        )}

        {/* Future User Credential Management & Profile Area */}
        <AccountDropdown
          currentUser={currentUser}
          username={username}
          onOpenAuthModal={onOpenAuthModal}
          showToast={showToast}
          selectedIde={selectedIde}
          onSelectIde={onSelectIde}
          language={language}
          onSelectLanguage={onSelectLanguage}
        />

        <div
          className={`engine-status-pill ${backendOnline ? 'online' : 'demo'}`}
          title={backendOnline ? 'Icarus Verilog connected & active' : 'Simulation running in demo mode'}
        >
          <span className="pulse-dot" />
          <span>{backendOnline ? 'iverilog' : 'Demo'}</span>
        </div>

        {currentView === 'workspace' && (
          <div className="nav-execution-buttons">
            <button
              className="run-sample-btn"
              onClick={onRunSample}
              disabled={loading || !canRun}
              title="Run Visible Sample Test Cases"
            >
              {loading ? '⏳' : '▶ Run'}
            </button>

            <button
              className="submit-full-btn"
              onClick={onSubmitFull}
              disabled={loading || !canRun}
              title="Submit against Full Hidden Verification Suite (Ctrl+Enter)"
            >
              {loading ? 'Simulating...' : '🚀 Submit'}
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
