import React, { useState } from 'react'
import VJCoinIcon from './VJCoinIcon'

export default function UserDashboard({
  stats,
  problems,
  onSelectProblem,
  onClaimDailyReward,
  onOpenStreakModal
}) {
  const [claiming, setClaiming] = useState(false)
  const [claimMsg, setClaimMsg] = useState('')
  const [claimError, setClaimError] = useState('')

  const username = stats?.username || 'RTL Verification Engineer'
  const streak = stats?.streak || 0
  const longestStreak = stats?.longest_streak || 0
  const coins = stats?.coins ?? 0
  const totalEarned = stats?.total_earned || 0
  const totalSpent = stats?.total_spent || 0
  const claimedToday = stats?.claimed_today || false
  const todayDate = stats?.today_date || ''
  const nextClaimDate = stats?.next_claim_date || ''
  const recentActivity = stats?.recent_activity || []
  const solvedCount = stats?.solved_count || 0
  const totalProblems = stats?.total_problems || problems.length
  const totalSubs = stats?.total_submissions || 0
  const accRate = stats?.acceptance_rate || 0
  const bookmarks = stats?.bookmarks || []
  const diffStats = stats?.difficulty_stats || {}
  const catStats = stats?.category_stats || {}
  const transactions = stats?.transactions || []
  const bookmarkedProblems = problems.filter(p => bookmarks.includes(p.id))

  async function handleClaim() {
    if (claiming || claimedToday || !onClaimDailyReward) return
    setClaiming(true)
    setClaimError('')
    try {
      const res = await onClaimDailyReward()
      if (res?.awarded || res?.coins_awarded) {
        setClaimMsg(`🎉 +${res.coins_awarded || 1} VJ Coin Claimed! (${res.streak || streak}-day streak)`)
        setTimeout(() => setClaimMsg(''), 4000)
      } else if (res?.already_claimed) {
        setClaimMsg(`✓ ${res.message || 'Already claimed for today.'}`)
        setTimeout(() => setClaimMsg(''), 3000)
      } else if (res?.error) {
        setClaimError(res.error)
      }
    } catch (err) {
      setClaimError(err.message || 'Could not complete claim request. Click retry.')
    } finally {
      setClaiming(false)
    }
  }

  return (
    <div className="dashboard-container">
      {/* Profile Overview Banner */}
      <div className="profile-banner">
        <div className="profile-left">
          <div className="avatar-circle">
            <span>⚡</span>
          </div>
          <div className="profile-titles">
            <h2>{username}</h2>
            <p className="profile-role">Digital Logic & RTL Verification Practitioner</p>
          </div>
        </div>

        <div className="profile-actions-right">
          <div
            className="profile-streak-pill clickable"
            onClick={onOpenStreakModal}
            title="Click to view Streak & Economy modal"
          >
            <span className="flame-icon">🔥</span>
            <div className="streak-meta">
              <span className="streak-count">{streak}-Day Streak</span>
              <span className="streak-sub">
                {claimedToday ? '✓ 1 VJ Coin claimed today' : '1 Coin ready to claim!'}
              </span>
            </div>
          </div>

          <div
            className="profile-coins-pill clickable"
            onClick={onOpenStreakModal}
            title="Click to view Coin Ledger"
          >
            <span className="coin-icon"><VJCoinIcon size={22} /></span>
            <div className="streak-meta">
              <span className="streak-count">{coins} {coins === 1 ? 'VJ Coin' : 'VJ Coins'}</span>
              <span className="streak-sub">Authoritative Balance</span>
            </div>
          </div>
        </div>
      </div>

      {/* Primary Streak & Currency Economics Panel (Requirement Section 3) */}
      <div className="dash-panel streak-system-panel">
        <div className="streak-panel-header">
          <div>
            <h3>🔥 Daily Streak & VJ Coin Economy</h3>
            <p className="panel-sub">
              Calculated via backend transactions on the <strong>Asia/Kolkata</strong> calendar. Missed days reset streak to 1.
            </p>
          </div>
          <div className="streak-today-badge">
            <span className="cal-icon">📅</span>
            <span>Date: {todayDate || 'Today'} (IST)</span>
          </div>
        </div>

        {/* 4 Stats Cards */}
        <div className="streak-metrics-grid">
          <div className="streak-metric-card highlight-flame">
            <span className="sm-label">Current Streak</span>
            <div className="sm-value">
              <span className="flame-emoji">🔥</span>
              <span className="val-text">{streak} {streak === 1 ? 'day' : 'days'}</span>
            </div>
            <span className="sm-foot">Consecutive practice days</span>
          </div>

          <div className="streak-metric-card">
            <span className="sm-label">Longest Streak</span>
            <div className="sm-value">
              <span className="val-text">🌟 {longestStreak} {longestStreak === 1 ? 'day' : 'days'}</span>
            </div>
            <span className="sm-foot">All-time record</span>
          </div>

          <div className="streak-metric-card highlight-coin">
            <span className="sm-label">Current Balance</span>
            <div className="sm-value">
              <span className="val-text"><VJCoinIcon size={24} /> {coins}</span>
            </div>
            <span className="sm-foot">Available to unlock solutions</span>
          </div>

          <div className="streak-metric-card">
            <span className="sm-label">Total Earned / Spent</span>
            <div className="sm-value sm-split">
              <span className="earned-val">+{totalEarned}</span>
              <span className="slash-div">/</span>
              <span className="spent-val">-{totalSpent}</span>
            </div>
            <span className="sm-foot">Lifetime coin audit</span>
          </div>
        </div>

        {/* Daily Reward Claim Card */}
        <div className="daily-reward-callout">
          <div className="reward-callout-left">
            <h4>Daily Login Reward (1 VJ Coin / Calendar Day)</h4>
            <p>
              {claimedToday
                ? `✓ You have received your 1 VJ Coin daily reward for ${todayDate}. Next eligible claim date: ${nextClaimDate || 'Tomorrow'} (Asia/Kolkata timezone).`
                : "You haven't claimed your daily reward yet today. Claim 1 VJ Coin now to maintain your practice streak!"}
            </p>
            {nextClaimDate && (
              <span className="next-claim-meta">
                📅 Next eligible claim date: <strong>{nextClaimDate}</strong>
              </span>
            )}
            {claimMsg && <span className="claim-toast-inline">{claimMsg}</span>}
            {claimError && (
              <div className="claim-error-box">
                <span>⚠️ {claimError}</span>
                <button className="retry-btn-inline" onClick={handleClaim}>Retry Claim</button>
              </div>
            )}
          </div>
          <button
            className={`daily-claim-action-btn ${claimedToday ? 'done' : 'ready'}`}
            disabled={claimedToday || claiming}
            onClick={handleClaim}
          >
            {claiming ? 'Verifying...' : claimedToday ? '✓ Claimed Today' : '🎁 Claim 1 VJ Coin'}
          </button>
        </div>

        {/* Recent Activity Calendar (Last 14 days) */}
        {recentActivity.length > 0 && (
          <div className="recent-activity-subpanel">
            <h5>Recent Activity History (Asia/Kolkata Calendar)</h5>
            <div className="activity-chips-row">
              {recentActivity.map((act, i) => (
                <div key={i} className="activity-chip-item">
                  <span className="act-date">{act.activity_date}</span>
                  <div className="act-badges">
                    <span className="act-coin-badge">
                      {act.daily_coin_awarded ? '🪙 +1 Coin' : '—'}
                    </span>
                    <span className="act-streak-badge">
                      🔥 {act.streak_count}d
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Metric Cards Row */}
      <div className="stats-metric-row">
        <div className="metric-card">
          <span className="metric-label">Solved Challenges</span>
          <div className="metric-val">
            <span className="num-large">{solvedCount}</span>
            <span className="denom">/ {totalProblems}</span>
          </div>
          <div className="metric-bar">
            <div
              className="metric-fill"
              style={{ width: `${totalProblems > 0 ? (solvedCount / totalProblems) * 100 : 0}%` }}
            />
          </div>
        </div>

        <div className="metric-card">
          <span className="metric-label">Acceptance Rate</span>
          <div className="metric-val">
            <span className="num-large">{accRate}%</span>
          </div>
          <span className="metric-foot">{stats?.accepted_submissions || 0} accepted of {totalSubs} submissions</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Total Submissions</span>
          <div className="metric-val">
            <span className="num-large">{totalSubs}</span>
          </div>
          <span className="metric-foot">Simulated on Icarus Verilog</span>
        </div>
      </div>

      <div className="dashboard-columns">
        {/* Left Col: Difficulty & Categories */}
        <div className="dash-col">
          {/* Difficulty Breakdown */}
          <div className="dash-panel">
            <h3>Difficulty Breakdown & Coin Rewards</h3>
            <div className="diff-breakdown-list">
              {[
                { name: 'Easy', rewardNote: '0 VJ Coins' },
                { name: 'Medium', rewardNote: '+1 VJ Coin' },
                { name: 'Hard', rewardNote: '+1 VJ Coin' }
              ].map(item => {
                const diff = item.name
                const stat = diffStats[diff] || { solved: 0, total: 1 }
                const pct = stat.total > 0 ? Math.round((stat.solved / stat.total) * 100) : 0
                return (
                  <div key={diff} className="diff-item">
                    <div className="diff-top">
                      <div>
                        <span className={`diff-name ${diff.toLowerCase()}`}>{diff}</span>
                        <span className="diff-reward-tag">({item.rewardNote})</span>
                      </div>
                      <span className="diff-count">{stat.solved} / {stat.total}</span>
                    </div>
                    <div className="diff-bar-track">
                      <div className={`diff-bar-fill ${diff.toLowerCase()}`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Category Progress */}
          <div className="dash-panel">
            <h3>Topic Mastery Progress</h3>
            <div className="cat-progress-list">
              {Object.entries(catStats).map(([cat, val]) => {
                const pct = val.total > 0 ? Math.round((val.solved / val.total) * 100) : 0
                return (
                  <div key={cat} className="cat-prog-item">
                    <div className="cat-top">
                      <span className="cat-title">{cat}</span>
                      <span className="cat-frac">{val.solved}/{val.total} ({pct}%)</span>
                    </div>
                    <div className="cat-bar-track">
                      <div className="cat-bar-fill" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Right Col: Bookmarks & Transactions */}
        <div className="dash-col">
          {/* Bookmarked Challenges */}
          <div className="dash-panel">
            <h3>Bookmarked Challenges ({bookmarkedProblems.length})</h3>
            {bookmarkedProblems.length === 0 ? (
              <p className="empty-dash-hint">You haven't bookmarked any problems yet. Click the star icon on any challenge to save it here.</p>
            ) : (
              <div className="bookmarked-list">
                {bookmarkedProblems.map(p => (
                  <div
                    key={p.id}
                    className="bookmarked-item"
                    onClick={() => onSelectProblem(p.id)}
                  >
                    <div>
                      <span className="b-title">{p.title}</span>
                      <div className="b-meta">
                        <span className={`diff-mini ${p.difficulty.toLowerCase()}`}>{p.difficulty}</span>
                        <span className="b-cat">{p.category}</span>
                      </div>
                    </div>
                    <button className="b-open-btn">Solve ➔</button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Currency Ledger Preview */}
          <div className="dash-panel">
            <div className="card-top-between">
              <h3>Coin Transaction History</h3>
              <button className="view-all-link" onClick={onOpenStreakModal}>Full Modal ➔</button>
            </div>
            {transactions.length === 0 ? (
              <p className="empty-dash-hint">No transactions recorded yet.</p>
            ) : (
              <div className="dash-tx-preview-list">
                {transactions.slice(0, 8).map((tx, idx) => (
                  <div key={idx} className="dash-tx-row">
                    <span className="tx-icon-mini">{tx.amount > 0 ? '🟢' : '🔴'}</span>
                    <span className="dash-tx-desc">{tx.description}</span>
                    <span className={`dash-tx-val ${tx.amount > 0 ? 'pos' : 'neg'}`}>
                      {tx.amount > 0 ? `+${tx.amount}` : tx.amount} VJ
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
