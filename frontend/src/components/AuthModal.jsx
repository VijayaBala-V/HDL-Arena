import React, { useState } from 'react'
import { apiFetchJson, setAuthToken, clearAuthToken } from '../utils/api'
import VJCoinIcon from './VJCoinIcon'

export default function AuthModal({
  isOpen,
  onClose,
  currentUser,
  onUserChanged,
  showToast = () => {}
}) {
  const [mode, setMode] = useState('login') // 'login' | 'status'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  if (!isOpen) return null

  async function handleLoginSubmit(e) {
    e.preventDefault()
    if (!username.trim() || !password.trim()) {
      setErrorMsg('Please enter both username and password.')
      return
    }

    setLoading(true)
    setErrorMsg('')

    try {
      const data = await apiFetchJson('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username: username.trim(),
          password: password.trim()
        })
      })

      if (!data.token) {
        throw new Error(data.error || 'Authentication failed. Please check credentials.')
      }

      setAuthToken(data.token)
      showToast(`⚡ Welcome, ${data.username}! Authenticated successfully.`)
      if (onUserChanged) {
        await onUserChanged(data.token)
      }
      onClose()
    } catch (err) {
      setErrorMsg(err.message || 'Login request failed. Server might be offline.')
    } finally {
      setLoading(false)
    }
  }

  function handleLogout() {
    clearAuthToken()
    showToast('Signed out of account. Session reverted to default.')
    if (onUserChanged) {
      onUserChanged(null)
    }
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card auth-modal-card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <span className="modal-title-icon">👤</span>
            <div>
              <h3>{currentUser ? 'Engineer Profile & Account' : 'Sign In to HDL Arena'}</h3>
              <p className="modal-sub">
                {currentUser
                  ? `Authenticated as ${currentUser.username} (ID: ${currentUser.user_id})`
                  : 'Log in to sync your VJ Coins, streaks and solutions across sessions.'}
              </p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} title="Close">✕</button>
        </div>

        <div className="modal-body">
          {errorMsg && (
            <div className="auth-error-banner">
              <span>⚠️ {errorMsg}</span>
              <button className="retry-mini-btn" onClick={handleLoginSubmit}>Retry</button>
            </div>
          )}

          {currentUser && (
            <div className="current-user-status-card">
              <div className="user-info-row">
                <div className="user-avatar-tag">⚡</div>
                <div>
                  <h4 className="active-uname">{currentUser.username}</h4>
                  <span className="active-uid">Account Token: {currentUser.token ? `${currentUser.token.slice(0, 14)}...` : 'Active'}</span>
                </div>
              </div>

              <div className="account-economy-summary">
                <div className="eco-pill">
                  <span className="eco-label">Balance</span>
                  <strong className="eco-val"><VJCoinIcon size={14} /> {currentUser.coins ?? 0} {currentUser.coins === 1 ? 'Coin' : 'Coins'}</strong>
                </div>
                <div className="eco-pill">
                  <span className="eco-label">Daily Streak</span>
                  <strong className="eco-val">🔥 {currentUser.streak ?? 0} Days</strong>
                </div>
                <div className="eco-pill">
                  <span className="eco-label">Today Status</span>
                  <strong className="eco-val">{currentUser.claimed_today ? '✓ Claimed' : '🎁 Unclaimed'}</strong>
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleLoginSubmit} className="auth-form-fields">
            <h4>{currentUser ? 'Switch / Sign In to Another Account' : 'Enter Credentials'}</h4>
            <div className="field-group">
              <label>Username</label>
              <input
                type="text"
                className="auth-input-box"
                placeholder="e.g. engineer, rajesh, verilog_pro"
                value={username}
                onChange={e => setUsername(e.target.value)}
                disabled={loading}
                autoComplete="username"
              />
            </div>

            <div className="field-group">
              <label>Password</label>
              <input
                type="password"
                className="auth-input-box"
                placeholder="Enter password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                disabled={loading}
                autoComplete="current-password"
              />
            </div>

            <p className="auth-hint-text">
              💡 <em>New usernames are automatically registered on first successful sign in.</em>
            </p>

            <div className="auth-modal-actions">
              {currentUser && (
                <button
                  type="button"
                  className="signout-btn"
                  onClick={handleLogout}
                  disabled={loading}
                >
                  Sign Out
                </button>
              )}
              <button
                type="submit"
                className="auth-submit-btn"
                disabled={loading}
              >
                {loading ? 'Authenticating...' : 'Sign In / Register'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
