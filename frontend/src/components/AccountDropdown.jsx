import React, { useState, useRef, useEffect } from 'react'

/**
 * Modular Account Dropdown Component
 * Prepares scalable architecture for future user account & credential management.
 */
export default function AccountDropdown({
  currentUser,
  username = 'Engineer',
  onOpenAuthModal,
  showToast = () => {},
  selectedIde = 'verilog',
  onSelectIde,
  language = 'verilog',
  onSelectLanguage
}) {
  const [isOpen, setIsOpen] = useState(false)
  const [activeModal, setActiveModal] = useState(null) // 'profile' | 'security' | 'preferences' | 'idePrefs'
  const dropdownRef = useRef(null)

  // Local storage for user preferences
  const [savedPreferences, setSavedPreferences] = useState(() => {
    try {
      const stored = localStorage.getItem('hdl_user_preferences')
      return stored ? JSON.parse(stored) : {
        editorTheme: 'vs-dark',
        autoFormatOnSave: true,
        wordWrap: false,
        keybinding: 'standard',
        defaultIde: 'verilog',
        defaultLanguage: 'verilog'
      }
    } catch {
      return {
        editorTheme: 'vs-dark',
        autoFormatOnSave: true,
        wordWrap: false,
        keybinding: 'standard',
        defaultIde: 'verilog',
        defaultLanguage: 'verilog'
      }
    }
  })

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Close on Escape key
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        setIsOpen(false)
        setActiveModal(null)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  function handleSavePreferences(updated) {
    const next = { ...savedPreferences, ...updated }
    setSavedPreferences(next)
    try {
      localStorage.setItem('hdl_user_preferences', JSON.stringify(next))
      showToast('✓ User preferences updated successfully!')
    } catch (e) {
      console.warn('Could not save preferences to localStorage')
    }
  }

  const userInitial = (username || 'E').charAt(0).toUpperCase()
  const displayEmail = currentUser?.email || `${(username || 'engineer').toLowerCase().replace(/\s+/g, '')}@hdlarena.dev`

  return (
    <div className="account-dropdown-wrapper" ref={dropdownRef}>
      {/* Top Navbar Compact Avatar Area */}
      <button
        type="button"
        className={`nav-account-btn ${isOpen ? 'active' : ''}`}
        onClick={() => setIsOpen(prev => !prev)}
        aria-expanded={isOpen}
        aria-haspopup="true"
        title="User Account & Settings"
      >
        <span className="account-avatar-circle">{userInitial}</span>
        <span className="account-name-label">{username || 'Engineer'}</span>
        <span className={`account-chevron ${isOpen ? 'open' : ''}`}>▾</span>
      </button>

      {/* Account Dropdown Menu */}
      {isOpen && (
        <div className="account-menu-flyout" role="menu">
          {/* Header Identity Card */}
          <div className="account-menu-header">
            <div className="account-header-avatar">{userInitial}</div>
            <div className="account-header-info">
              <span className="account-user-name">{username || 'Engineer'}</span>
              <span className="account-user-email">{displayEmail}</span>
              <span className="account-role-badge">RTL Verification Engineer</span>
            </div>
          </div>

          <div className="account-menu-divider" />

          {/* Account Actions Section */}
          <div className="account-menu-list">
            <button
              type="button"
              className="account-menu-item"
              role="menuitem"
              onClick={() => {
                setIsOpen(false)
                setActiveModal('profile')
              }}
            >
              <span className="menu-item-icon">👤</span>
              <div className="menu-item-col">
                <span className="menu-item-title">User Profile</span>
                <span className="menu-item-desc">Personal details and public identity</span>
              </div>
            </button>

            <button
              type="button"
              className="account-menu-item"
              role="menuitem"
              onClick={() => {
                setIsOpen(false)
                setActiveModal('security')
              }}
            >
              <span className="menu-item-icon">🔑</span>
              <div className="menu-item-col">
                <span className="menu-item-title">Password & Credentials</span>
                <span className="menu-item-desc">Security keys and authentication settings</span>
              </div>
            </button>

            <button
              type="button"
              className="account-menu-item"
              role="menuitem"
              onClick={() => {
                setIsOpen(false)
                setActiveModal('preferences')
              }}
            >
              <span className="menu-item-icon">⚙️</span>
              <div className="menu-item-col">
                <span className="menu-item-title">Account Preferences</span>
                <span className="menu-item-desc">Theme, keybindings & editor defaults</span>
              </div>
            </button>

            <button
              type="button"
              className="account-menu-item"
              role="menuitem"
              onClick={() => {
                setIsOpen(false)
                setActiveModal('idePrefs')
              }}
            >
              <span className="menu-item-icon">🛠️</span>
              <div className="menu-item-col">
                <span className="menu-item-title">Saved IDE & Language</span>
                <span className="menu-item-desc">Default simulation environment & dialect</span>
              </div>
            </button>
          </div>

          <div className="account-menu-divider" />

          {/* Footer Auth Action */}
          <div className="account-menu-footer">
            <button
              type="button"
              className="account-auth-action-btn"
              onClick={() => {
                setIsOpen(false)
                if (onOpenAuthModal) onOpenAuthModal()
              }}
            >
              <span className="menu-item-icon">🚪</span>
              <span>{currentUser ? 'Switch Account / Sign Out' : 'Sign In / Register'}</span>
            </button>
          </div>
        </div>
      )}

      {/* Modular Modals for Future Account Management */}
      {activeModal && (
        <div className="account-modal-backdrop" onClick={() => setActiveModal(null)}>
          <div className="account-dialog-card" onClick={e => e.stopPropagation()}>
            <div className="account-dialog-header">
              <h3>
                {activeModal === 'profile' && '👤 User Profile'}
                {activeModal === 'security' && '🔑 Password & Credentials Management'}
                {activeModal === 'preferences' && '⚙️ User Preferences'}
                {activeModal === 'idePrefs' && '🛠️ Saved IDE & Language Preferences'}
              </h3>
              <button
                type="button"
                className="dialog-close-btn"
                onClick={() => setActiveModal(null)}
                aria-label="Close dialog"
              >
                ✕
              </button>
            </div>

            <div className="account-dialog-body">
              {activeModal === 'profile' && (
                <div className="dialog-fields-group">
                  <div className="form-field-row">
                    <label>Username</label>
                    <input
                      type="text"
                      className="dialog-input"
                      value={username || 'Engineer'}
                      readOnly
                    />
                  </div>
                  <div className="form-field-row">
                    <label>Email Address</label>
                    <input
                      type="email"
                      className="dialog-input"
                      value={displayEmail}
                      readOnly
                    />
                  </div>
                  <div className="form-field-row">
                    <label>Designation / Role</label>
                    <input
                      type="text"
                      className="dialog-input"
                      value="Digital IC & RTL Verification Engineer"
                      readOnly
                    />
                  </div>
                  <p className="dialog-note">
                    ℹ️ Backend credential sync is reserved for production deployment. Profile is stored with your session identity.
                  </p>
                </div>
              )}

              {activeModal === 'security' && (
                <div className="dialog-fields-group">
                  <div className="form-field-row">
                    <label>Current Password</label>
                    <input
                      type="password"
                      className="dialog-input"
                      placeholder="••••••••••••"
                      disabled
                    />
                  </div>
                  <div className="form-field-row">
                    <label>New Password</label>
                    <input
                      type="password"
                      className="dialog-input"
                      placeholder="Enter new secure passphrase"
                      disabled
                    />
                  </div>
                  <div className="security-notice-card">
                    <span className="notice-icon">🛡️</span>
                    <div>
                      <strong>Authentication Architecture Ready</strong>
                      <p>
                        This module is structurally decoupled from platform logic. Integration with OAuth2/JWT or LDAP authentication requires zero refactoring of frontend views.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {activeModal === 'preferences' && (
                <div className="dialog-fields-group">
                  <div className="form-field-row">
                    <label>Color Theme</label>
                    <select
                      className="dialog-input"
                      value={savedPreferences.editorTheme}
                      onChange={e => handleSavePreferences({ editorTheme: e.target.value })}
                    >
                      <option value="vs-dark">Modern EDA Dark (Default)</option>
                      <option value="high-contrast">High-Contrast Dark</option>
                      <option value="nord">Nordic Studio</option>
                    </select>
                  </div>
                  <div className="form-field-row">
                    <label>Auto-Format on Save</label>
                    <select
                      className="dialog-input"
                      value={savedPreferences.autoFormatOnSave ? 'yes' : 'no'}
                      onChange={e => handleSavePreferences({ autoFormatOnSave: e.target.value === 'yes' })}
                    >
                      <option value="yes">Enabled (Deterministic 4-space indent)</option>
                      <option value="no">Disabled</option>
                    </select>
                  </div>
                </div>
              )}

              {activeModal === 'idePrefs' && (
                <div className="dialog-fields-group">
                  <div className="form-field-row">
                    <label>Default Simulation IDE</label>
                    <select
                      className="dialog-input"
                      value={savedPreferences.defaultIde}
                      onChange={e => {
                        handleSavePreferences({ defaultIde: e.target.value })
                        if (onSelectIde) onSelectIde(e.target.value)
                      }}
                    >
                      <option value="verilog">Verilog / HDL IDE (Icarus Verilog)</option>
                      <option value="cpp">C / C++ IDE (Clang Engine)</option>
                      <option value="python">Python IDE (Cocotb & Scripting)</option>
                      <option value="java">Java IDE (JVM Architecture)</option>
                    </select>
                  </div>
                  <div className="form-field-row">
                    <label>Default HDL Dialect</label>
                    <select
                      className="dialog-input"
                      value={savedPreferences.defaultLanguage}
                      onChange={e => {
                        handleSavePreferences({ defaultLanguage: e.target.value })
                        if (onSelectLanguage) onSelectLanguage(e.target.value)
                      }}
                    >
                      <option value="verilog">Verilog (IEEE 1364)</option>
                      <option value="systemverilog">SystemVerilog (IEEE 1800)</option>
                    </select>
                  </div>
                  <p className="dialog-note">
                    ✓ Saved preferences will be automatically applied whenever you open new challenges.
                  </p>
                </div>
              )}
            </div>

            <div className="account-dialog-footer">
              <button
                type="button"
                className="dialog-dismiss-btn"
                onClick={() => setActiveModal(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
