import React, { useState } from 'react'
import VJCoinIcon from './VJCoinIcon'

export default function StreakRewardsModal({
  isOpen,
  onClose,
  stats,
  onClaimDailyReward
}) {
  const [claiming, setClaiming] = useState(false)
  const [claimSuccessMsg, setClaimSuccessMsg] = useState('')
  const [claimErrorMsg, setClaimErrorMsg] = useState('')

  if (!isOpen) return null

  const streak = stats?.streak || 0
  const longestStreak = stats?.longest_streak || 0
  const coins = stats?.coins ?? 0
  const formattedCoins = typeof coins === 'number' ? (Number.isInteger(coins) ? coins : coins.toFixed(1)) : coins
  const totalEarned = stats?.total_earned || 0
  const totalSpent = stats?.total_spent || 0
  const claimedToday = stats?.claimed_today || false
  const todayDate = stats?.today_date || ''
  const nextClaimDate = stats?.next_claim_date || ''
  const transactions = stats?.transactions || []
  const recentActivity = stats?.recent_activity || []

  async function handleClaim() {
    if (claiming || claimedToday || !onClaimDailyReward) return
    setClaiming(true)
    setClaimErrorMsg('')
    try {
      const res = await onClaimDailyReward()
      if (res?.awarded || res?.coins_awarded) {
        setClaimSuccessMsg(`🎉 Claimed +${res.coins_awarded || 1} VJ Coin! ${res.streak || streak}-day streak active!`)
        setTimeout(() => setClaimSuccessMsg(''), 4000)
      } else if (res?.already_claimed) {
        setClaimSuccessMsg(`✓ ${res.message || 'Already claimed today.'}`)
        setTimeout(() => setClaimSuccessMsg(''), 3500)
      } else if (res?.error) {
        setClaimErrorMsg(res.error)
      }
    } catch (err) {
      setClaimErrorMsg(err.message || 'Failed to claim. Please click retry.')
    } finally {
      setClaiming(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card streak-rewards-modal" onClick={e => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title-row">
            <span className="modal-title-icon">🔥</span>
            <div>
              <h3>Daily Streak & VJ Coin Rewards</h3>
              <p className="modal-sub">Practice digital logic daily on the Asia/Kolkata calendar to earn VJ Coins.</p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} title="Close">✕</button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* Top Hero Stats */}
          <div className="streak-hero-banner">
            <div className="hero-streak-col">
              <span className="hero-number">🔥 {streak} {streak === 1 ? 'Day' : 'Days'}</span>
              <span className="hero-label">Current Streak</span>
            </div>
            <div className="hero-divider" />
            <div className="hero-streak-col">
              <span className="hero-number">🌟 {longestStreak} {longestStreak === 1 ? 'Day' : 'Days'}</span>
              <span className="hero-label">Longest Streak</span>
            </div>
            <div className="hero-divider" />
            <div className="hero-coins-col">
              <span className="hero-number"><VJCoinIcon size={22} /> {formattedCoins}</span>
              <span className="hero-label">{coins === 1 ? 'VJ Coin' : 'VJ Coins'}</span>
            </div>
          </div>

          {/* Daily Claim Banner */}
          <div className="daily-claim-card">
            {claimSuccessMsg && (
              <div className="claim-celebration-toast">
                {claimSuccessMsg}
              </div>
            )}

            <div className="claim-card-inner">
              <div className="claim-text-col">
                <h4>Daily Login Reward (1 VJ Coin)</h4>
                <p>
                  {claimedToday
                    ? `✓ Today's daily reward of 1 VJ Coin has been claimed for ${todayDate}. Next eligible claim date: ${nextClaimDate || 'Tomorrow'} (Asia/Kolkata timezone).`
                    : "Log in and check in each calendar day (Asia/Kolkata timezone) to receive 1 VJ Coin and build your streak."}
                </p>
                {nextClaimDate && (
                  <span className="next-claim-meta">
                    📅 Next eligible claim: <strong>{nextClaimDate}</strong>
                  </span>
                )}
                {claimErrorMsg && (
                  <div className="claim-error-box">
                    <span>⚠️ {claimErrorMsg}</span>
                    <button className="retry-btn-inline" onClick={handleClaim}>Retry Claim</button>
                  </div>
                )}
              </div>

              <button
                className={`daily-claim-btn ${claimedToday ? 'claimed' : 'ready'}`}
                disabled={claimedToday || claiming}
                onClick={handleClaim}
              >
                {claiming
                  ? 'Verifying...'
                  : claimedToday
                  ? '✓ Claimed Today'
                  : '🎁 Claim 1 VJ Coin'}
              </button>
            </div>
          </div>

          {/* Coin Earning & Spending Rules */}
          <div className="economy-guide-grid">
            <div className="economy-box earn-box">
              <h6>⚡ How to Earn VJ Coins</h6>
              <ul>
                <li>Daily Login (Asia/Kolkata): <strong>+1 VJ Coin</strong></li>
                <li>Medium / Hard / Advanced / Expert First Solve: <strong>+1 VJ Coin</strong></li>
                <li>Beginner Challenges: <em>0 VJ Coins (Skill Practice)</em></li>
                <li><em>Note: Only verified first-time completions qualify.</em></li>
              </ul>
            </div>

            <div className="economy-box spend-box">
              <h6>🔓 How to Spend VJ Coins</h6>
              <ul>
                <li>Unlock Progressive Clue: <strong>0.5 VJ Coin</strong></li>
                <li>Unlock Full Canonical Solution: <strong>1.0 VJ Coin</strong></li>
                <li>Permanent unlock: Once unlocked, view freely anytime.</li>
              </ul>
            </div>
          </div>

          {/* Recent Calendar Activity */}
          {recentActivity.length > 0 && (
            <div className="streak-calendar-section">
              <h5>Recent Activity Calendar (Asia/Kolkata)</h5>
              <div className="activity-chips-row">
                {recentActivity.slice(0, 7).map((act, idx) => (
                  <div key={idx} className="activity-chip-item">
                    <span className="act-date">{act.activity_date}</span>
                    <div className="act-badges">
                      <span className="act-coin-badge">{act.daily_coin_awarded ? <><VJCoinIcon size={12} /> +1</> : '—'}</span>
                      <span className="act-streak-badge">🔥 {act.streak_count}d</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Transaction Ledger */}
          <div className="transactions-ledger-section">
            <div className="card-top-between">
              <h5>Coin Transaction History</h5>
              <span className="tx-summary-chip">Earned: +{totalEarned} | Spent: -{totalSpent}</span>
            </div>
            {transactions.length === 0 ? (
              <p className="no-tx-hint">No transactions recorded yet.</p>
            ) : (
              <div className="tx-list">
                {transactions.slice(0, 10).map((tx, idx) => (
                  <div key={idx} className="tx-row">
                    <div className="tx-desc-col">
                      <span className="tx-icon">
                        {tx.amount > 0 ? '🟢' : '🔴'}
                      </span>
                      <span className="tx-desc">{tx.description}</span>
                    </div>
                    <div className="tx-right-col">
                      <span className={`tx-amount ${tx.amount > 0 ? 'pos' : 'neg'}`}>
                        {tx.amount > 0 ? `+${tx.amount}` : tx.amount} VJ
                      </span>
                      <span className="tx-time">
                        {tx.created_at ? new Date(tx.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : ''}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <button className="done-btn" onClick={onClose}>
            Back to Workspace
          </button>
        </div>
      </div>
    </div>
  )
}
