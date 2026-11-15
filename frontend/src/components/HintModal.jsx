import React, { useState } from 'react'
import VJCoinIcon from './VJCoinIcon'

export default function HintModal({
  isOpen,
  onClose,
  problem,
  hints = [],
  progressiveHints = [],
  coinBalance = 0,
  onUnlockHint,
  showToast = () => {}
}) {
  const [confirmUnlockIdx, setConfirmUnlockIdx] = useState(null)
  const [unlocking, setUnlocking] = useState(false)

  if (!isOpen) return null

  // Format coin balance cleanly (exact half-coins, e.g. 2.5)
  const formattedBalance = (typeof coinBalance === 'number')
    ? (Number.isInteger(coinBalance) ? coinBalance.toFixed(0) : coinBalance.toFixed(1))
    : '0'

  // Build unified hints array
  let effectiveProgressive = progressiveHints
  if (!effectiveProgressive || effectiveProgressive.length === 0) {
    // Generate default 3-stage progressive hints from basic hints
    const baseList = (hints && hints.length > 0) ? hints : [
      `Review module port declaration for '${problem?.module_name || 'DUT'}' and ensure widths match.`,
      problem?.ports?.some(p => p.name === 'rst' || p.name === 'clk')
        ? 'Ensure reset behavior (synchronous vs asynchronous) strictly matches the active-high/low clocking requirement.'
        : 'Review sensitivity lists and ensure all output paths are assigned to avoid inferred latches.',
      'Test edge conditions: maximum rollover count, zero reset hold, and simultaneous assertion.'
    ]
    effectiveProgressive = baseList.map((text, idx) => ({
      index: idx,
      cost: idx === 0 ? 0.0 : 0.5,
      title: idx === 0 ? 'Conceptual Nudge (Free)' : `Implementation Clue ${idx} (0.5 VJ)`,
      is_unlocked: idx === 0,
      text: idx === 0 ? text : (typeof text === 'string' && !text.startsWith('🔒') ? text : '')
    }))
  }

  async function handleConfirmUnlock(idx, cost) {
    if (coinBalance < cost) {
      showToast(`⚠️ Insufficient VJ Coins (Balance: ${formattedBalance} VJ). Earn +1 VJ with Daily Login!`)
      return
    }

    setUnlocking(true)
    try {
      if (onUnlockHint) {
        await onUnlockHint(idx)
      }
      setConfirmUnlockIdx(null)
      showToast(`💡 Unlocked Hint ${idx + 1} (-${cost} VJ Coin)!`)
    } catch (err) {
      showToast(err.message || 'Failed to unlock hint.')
    } finally {
      setUnlocking(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="hint-modal-title">
      <div className="modal-card hint-modal-card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <span className="modal-title-icon" aria-hidden="true">💡</span>
            <div>
              <h3 id="hint-modal-title">Progressive Hints: {problem?.title}</h3>
              <p className="modal-sub">Step-by-step guidance • First hint free, subsequent clues 0.5 VJ</p>
            </div>
          </div>
          <div className="modal-header-right">
            <div className="hint-modal-balance-pill" title="Your current VJ Coin Balance">
              <VJCoinIcon size={16} />
              <span className="coin-val">{formattedBalance} VJ</span>
            </div>
            <button className="modal-close-btn" onClick={onClose} title="Close hints" aria-label="Close hints">✕</button>
          </div>
        </div>

        <div className="modal-body">
          <div className="hint-steps-list">
            {effectiveProgressive.map((hint, i) => {
              const isUnlocked = hint.is_unlocked || hint.cost === 0
              const cost = hint.cost || 0.5
              const isConfirming = confirmUnlockIdx === hint.index
              const hasSufficientCoins = coinBalance >= cost

              return (
                <div key={hint.index ?? i} className={`hint-step-item ${isUnlocked ? 'unlocked' : 'locked'}`}>
                  <div className="hint-step-header-row">
                    <div className="hint-step-badge">
                      {isUnlocked ? '✓' : '🔒'} {hint.title || `Hint ${i + 1}`}
                    </div>
                    {isUnlocked ? (
                      <span className="hint-status-pill unlocked">Revealed</span>
                    ) : (
                      <span className="hint-status-pill locked">{cost} VJ Coin</span>
                    )}
                  </div>

                  <div className="hint-step-content">
                    {isUnlocked ? (
                      <p className="revealed-hint-text">{hint.text}</p>
                    ) : (
                      <div className="locked-hint-container">
                        {!isConfirming ? (
                          <div className="locked-action-row">
                            <p className="hint-teaser-text">
                              {hint.teaser || 'Unlocks an architectural clue, timing diagram tip, or implementation guidance.'}
                            </p>
                            <button
                              type="button"
                              className="get-hint-btn"
                              onClick={() => setConfirmUnlockIdx(hint.index)}
                            >
                              💡 Get Hint — {cost} VJ
                            </button>
                          </div>
                        ) : (
                          <div className="hint-confirm-box">
                            <div className="confirm-prompt-text">
                              <strong>Confirm Deduction:</strong> Unlock this hint for <strong>{cost} VJ Coin</strong>?
                              <br />
                              <span className="balance-preview-text">
                                Current Balance: <strong>{formattedBalance} VJ</strong>
                                {hasSufficientCoins
                                  ? ` ➔ Remaining after unlock: ${(coinBalance - cost).toFixed(1)} VJ`
                                  : ` ⚠️ (Need 0.5 VJ)`}
                              </span>
                            </div>

                            {!hasSufficientCoins ? (
                              <div className="insufficient-coins-warning">
                                <span>⚠️ You need {cost} VJ Coin to unlock this clue. Earn +1 VJ by claiming your Daily Streak Reward or by solving Medium/Hard problems!</span>
                              </div>
                            ) : null}

                            <div className="confirm-btn-actions">
                              {hasSufficientCoins && (
                                <button
                                  type="button"
                                  className="confirm-unlock-btn"
                                  disabled={unlocking}
                                  onClick={() => handleConfirmUnlock(hint.index, cost)}
                                >
                                  {unlocking ? 'Unlocking...' : `Confirm & Deduct ${cost} VJ`}
                                </button>
                              )}
                              <button
                                type="button"
                                className="cancel-confirm-btn"
                                onClick={() => setConfirmUnlockIdx(null)}
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          <div className="hint-reminder-box">
            <span>💡 <em>Unlocked hints remain permanently available on your account without re-charging.</em></span>
          </div>
        </div>

        <div className="modal-footer">
          <button className="done-btn" onClick={onClose}>
            Back to Challenge
          </button>
        </div>
      </div>
    </div>
  )
}
