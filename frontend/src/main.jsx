import React, { useState, useEffect, useMemo, useRef } from 'react'
import { createRoot } from 'react-dom/client'
import { FALLBACK_PROBLEMS } from './data/fallbackProblems'
import Navbar from './components/Navbar'
import MultiFileEditor from './components/MultiFileEditor'
import SpecPanel from './components/SpecPanel'
import WaveformViewer from './components/WaveformViewer'
import DebugAdvisor from './components/DebugAdvisor'
import ProblemCatalog from './components/ProblemCatalog'
import LearningPaths from './components/LearningPaths'
import UserDashboard from './components/UserDashboard'
import StreakRewardsModal from './components/StreakRewardsModal'
import AuthModal from './components/AuthModal'
import HintModal from './components/HintModal'
import { apiFetchJson, getAuthToken, setAuthToken, clearAuthToken, fetchUserCoins, fetchProblemHints, unlockPaidHint } from './utils/api'
import { IDE_ENVIRONMENTS, getLanguagesForIde, getIdeForLanguage, isLanguageSupported } from './data/environments'
import VJCoinIcon from './components/VJCoinIcon'
import './style.css'

function App() {
  const [currentView, setCurrentView] = useState('workspace') // 'workspace' | 'problems' | 'tracks' | 'dashboard'
  const [problems, setProblems] = useState(FALLBACK_PROBLEMS)
  const [currentId, setCurrentId] = useState('counter4')
  const [backendOnline, setBackendOnline] = useState(false)

  // Environment & IDE selection state
  const [selectedIde, setSelectedIde] = useState('verilog')
  const [outputSize, setOutputSize] = useState('540') // '540' | '640' | '840'

  // Multi-file editor state (initialized immediately with counter4.v so typing works from t=0)
  const [files, setFiles] = useState(FALLBACK_PROBLEMS[0].starter_files)
  const [activeFileName, setActiveFileName] = useState('counter4.v')
  const [language, setLanguage] = useState('verilog')
  const [fontSize, setFontSize] = useState(13)

  // Non-coding question answering state (MCQ, Predict Output, Rubrics)
  const [selectedChoice, setSelectedChoice] = useState('')
  const [selectedChoices, setSelectedChoices] = useState([])
  const [predictAnswer, setPredictAnswer] = useState('')
  const [rubricAnswer, setRubricAnswer] = useState('')

  // Track currently loaded problem to prevent wiping user code during background fetches
  const loadedProblemRef = useRef('counter4')

  // Auth & authoritative economy state
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [currentUser, setCurrentUser] = useState(null)
  const [coinBalance, setCoinBalance] = useState(null) // null while loading/error, never fake 0
  const [coinLoading, setCoinLoading] = useState(true)
  const [coinError, setCoinError] = useState(null)
  const [animateCoins, setAnimateCoins] = useState(false)
  const [streakModalOpen, setStreakModalOpen] = useState(false)
  const [currentSolution, setCurrentSolution] = useState(null)
  const [isCurrentUnlocked, setIsCurrentUnlocked] = useState(false)

  // Architectural Hints state
  const [hintModalOpen, setHintModalOpen] = useState(false)
  const [hints, setHints] = useState([])

  // Simulation execution state
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [activeBottomTab, setActiveBottomTab] = useState('tests') // 'tests' | 'cycles' | 'waveform' | 'debug' | 'console'
  const [targetWaveformTime, setTargetWaveformTime] = useState(null)
  const [bottomHeight, setBottomHeight] = useState('normal') // 'normal' | 'expanded'

  // User and History state
  const [history, setHistory] = useState([])
  const [userStats, setUserStats] = useState(null)
  const [toast, setToast] = useState(null)
  const toastTimerRef = useRef(null)

  function isReducedMotion() {
    if (typeof window === 'undefined' || !window.matchMedia) return false
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches
  }

  function showToast(msg, customType = 'info') {
    if (toastTimerRef.current) {
      clearTimeout(toastTimerRef.current)
    }
    const message = typeof msg === 'string' ? msg : (msg?.message || String(msg || ''))
    if (!message) return

    let type = customType
    if (typeof msg === 'object' && msg?.type) {
      type = msg.type
    } else if (message.startsWith('⚠️') || message.toLowerCase().includes('failed') || message.toLowerCase().includes('error')) {
      type = 'error'
    } else if (message.startsWith('✓') || message.startsWith('🎉') || message.startsWith('🏆') || message.startsWith('✨') || message.startsWith('🔓')) {
      type = 'success'
    } else if (message.startsWith('💡') || message.startsWith('⚡')) {
      type = 'info'
    }

    setToast({ message, type })
    toastTimerRef.current = setTimeout(() => setToast(null), 3800)
  }

  // Trigger subtle balance pulse animation on coin changes (skips if reduced-motion preferred)
  function triggerCoinPulse() {
    if (isReducedMotion()) return
    setAnimateCoins(true)
    setTimeout(() => setAnimateCoins(false), 1200)
  }

  // Authoritative Coin Fetcher
  async function refreshCoinBalance(silent = false) {
    if (!silent) {
      setCoinLoading(true)
      setCoinError(null)
    }
    try {
      const data = await fetchUserCoins()
      setCoinBalance(data.coins)
      setCoinLoading(false)
      setCoinError(null)
      setUserStats(prev => ({
        ...(prev || {}),
        coins: data.coins,
        streak: data.streak ?? prev?.streak ?? 0,
        claimed_today: data.claimed_today ?? prev?.claimed_today ?? false,
        today_date: data.today_date,
        next_claim_date: data.next_claim_date
      }))
      return data
    } catch (err) {
      const msg = err.message || 'Failed to fetch VJ Coin balance.'
      console.error('[HDL Arena] VJ Coin fetch failed:', err)
      setCoinError(msg)
      setCoinLoading(false)
      if (!silent) {
        showToast(`⚠️ ${msg}`)
      }
      throw err
    }
  }

  // Active problem object
  const currentProblem = useMemo(() => {
    return problems.find(p => p.id === currentId) || problems[0] || FALLBACK_PROBLEMS[0]
  }, [problems, currentId])

  // 1. Initial load: authenticate user session and load problems, coins & stats
  useEffect(() => {
    async function initPlatformSession() {
      // Step A: Fetch Authoritative VJ Coin balance
      try {
        await refreshCoinBalance(true)
      } catch (err) {
        // Non-blocking: coinError state will show retry option in header
      }

      // Step B: Authenticate / fetch current user using stored token if present
      try {
        const me = await apiFetchJson('/api/account/me')
        setCurrentUser(me)
        if (me && me.token && !getAuthToken()) {
          setAuthToken(me.token)
        }
        if (me && me.coins !== undefined && typeof me.coins === 'number') {
          setCoinBalance(me.coins)
          setCoinLoading(false)
          setCoinError(null)
        }
      } catch (e) {
        console.warn('[HDL Arena] /api/account/me non-blocking:', e.message)
      }

      // Step C: Fetch comprehensive user stats (authoritative coins, streaks, completions)
      try {
        const stats = await apiFetchJson('/api/user/stats')
        setUserStats(stats)
        if (stats && stats.coins !== undefined && typeof stats.coins === 'number') {
          setCoinBalance(stats.coins)
          setCoinLoading(false)
          setCoinError(null)
        }
      } catch (e) {
        console.warn('[HDL Arena] /api/user/stats non-blocking:', e.message)
      }

      // Step D: Fetch problem list
      try {
        const data = await apiFetchJson('/api/problems')
        if (Array.isArray(data) && data.length > 0) {
          const merged = data.map(backendP => {
            const fallback = FALLBACK_PROBLEMS.find(f => f.id === backendP.id)
            return { ...(fallback || {}), ...backendP }
          })
          setProblems(merged)
          setBackendOnline(true)
        }
      } catch (e) {
        setBackendOnline(false)
      }
    }

    initPlatformSession()
  }, [])

  // Handle user authentication or account switch
  async function handleUserChanged(newToken) {
    if (newToken) {
      setAuthToken(newToken)
    } else {
      clearAuthToken()
    }

    // Refresh coins immediately for the authenticated identity
    try {
      await refreshCoinBalance(false)
      triggerCoinPulse()
    } catch (e) {}

    try {
      const me = await apiFetchJson('/api/account/me')
      setCurrentUser(me)
    } catch (e) {}

    try {
      const s = await apiFetchJson('/api/user/stats')
      setUserStats(s)
    } catch (e) {}

    try {
      // Re-fetch solution unlock status for active problem
      const pData = await apiFetchJson(`/api/problems/${currentId}`)
      setIsCurrentUnlocked(Boolean(pData.is_unlocked))
      if (pData.is_unlocked) {
        try {
          const solData = await apiFetchJson(`/api/problems/${currentId}/solution`)
          if (solData.solution) setCurrentSolution(solData.solution)
        } catch (e) {}
      } else {
        setCurrentSolution(null)
      }
    } catch (e) {}
  }

  // 2. Fetch full problem details and saved draft ONLY when problem ID changes
  useEffect(() => {
    if (!currentId) return

    if (loadedProblemRef.current === currentId && Object.keys(files).length > 0) {
      return
    }
    loadedProblemRef.current = currentId

    const targetProblem = problems.find(p => p.id === currentId) || FALLBACK_PROBLEMS.find(p => p.id === currentId) || FALLBACK_PROBLEMS[0]

    // Sync active editor environment and language with problem language
    if (targetProblem.language) {
      const ide = getIdeForLanguage(targetProblem.language)
      setSelectedIde(ide)
      setLanguage(targetProblem.language)
    }

    // Reset non-coding answer fields
    setSelectedChoice('')
    setSelectedChoices([])
    setPredictAnswer('')
    setRubricAnswer('')

    apiFetchJson(`/api/problems/${currentId}`)
      .then(data => {
        if (data.language) {
          const ide = getIdeForLanguage(data.language)
          setSelectedIde(ide)
          setLanguage(data.language)
        }
        if (data.progressive_hints && data.progressive_hints.length > 0) {
          setHints(data.progressive_hints)
        }
        const hasValidDraft = data.saved_draft &&
          typeof data.saved_draft === 'object' &&
          Object.keys(data.saved_draft).length > 0 &&
          Object.values(data.saved_draft).some(v => typeof v === 'string' && v.trim().length > 0)

        const hasValidStarter = data.starter_files &&
          typeof data.starter_files === 'object' &&
          Object.keys(data.starter_files).length > 0

        const targetStarter = targetProblem.starter_files || FALLBACK_PROBLEMS[0].starter_files || {}

        const starter = hasValidDraft
          ? data.saved_draft
          : (hasValidStarter ? data.starter_files : targetStarter)

        setFiles(starter)
        const firstFile = Object.keys(starter)[0] || `${targetProblem.module_name}.v`
        setActiveFileName(firstFile)
        setBackendOnline(true)

        // Set unlock state
        const unlocked = Boolean(data.is_unlocked)
        setIsCurrentUnlocked(unlocked)

        // If unlocked, fetch trusted canonical solution from backend
        if (unlocked) {
          apiFetchJson(`/api/problems/${currentId}/solution`)
            .then(solData => {
              if (solData.solution) setCurrentSolution(solData.solution)
            })
            .catch(() => {})
        } else {
          setCurrentSolution(null)
        }
      })
      .catch(() => {
        const starter = targetProblem.starter_files || FALLBACK_PROBLEMS[0].starter_files || {}
        setFiles(starter)
        const firstFile = Object.keys(starter)[0] || `${targetProblem.module_name}.v`
        setActiveFileName(firstFile)
        setIsCurrentUnlocked(false)
        setCurrentSolution(null)
      })

    // Fetch submission history for problem
    apiFetchJson(`/api/submissions/${currentId}`)
      .then(records => {
        if (Array.isArray(records)) setHistory(records)
      })
      .catch(() => {})

    // Pre-fetch architectural hints for current problem
    fetchProblemHints(currentId)
      .then(loadedHints => {
        if (loadedHints && loadedHints.length > 0) setHints(loadedHints)
      })
      .catch(() => {})

    setResult(null)
    setError('')
    setTargetWaveformTime(null)
  }, [currentId])

  // Change code in active file
  function handleChangeCode(fileName, newContent) {
    setFiles(prev => ({
      ...prev,
      [fileName]: newContent
    }))
  }

  // Reset active file to initial problem template
  function handleResetCode() {
    const defaultStarter = currentProblem.starter_files?.[activeFileName]
    if (defaultStarter !== undefined) {
      handleChangeCode(activeFileName, defaultStarter)
      showToast(`Reset ${activeFileName} to default starter template`)
    } else {
      const firstStarter = Object.values(currentProblem.starter_files || {})[0] || ''
      handleChangeCode(activeFileName, firstStarter)
    }
    setResult(null)
    setError('')
  }

  // Save draft
  async function handleSaveDraft() {
    try {
      await apiFetchJson(`/api/drafts/${currentId}`, {
        method: 'POST',
        body: JSON.stringify({ files })
      })
      showToast('Draft saved successfully!')
    } catch {
      showToast('Draft saved in local session.')
    }
  }

  // Restore snapshot from history
  function handleRestoreSnapshot(codeSnapshot) {
    if (!codeSnapshot) return
    try {
      const parsed = typeof codeSnapshot === 'string' ? JSON.parse(codeSnapshot) : codeSnapshot
      if (typeof parsed === 'object') {
        setFiles(parsed)
        const first = Object.keys(parsed)[0]
        if (first) setActiveFileName(first)
        showToast('Restored previous submission snapshot!')
      }
    } catch {
      if (typeof codeSnapshot === 'string') {
        handleChangeCode(activeFileName, codeSnapshot)
        showToast('Restored previous submission snapshot!')
      }
    }
  }

  // Toggle bookmark
  async function handleToggleBookmark(problemId) {
    try {
      const data = await apiFetchJson('/api/user/bookmark', {
        method: 'POST',
        body: JSON.stringify({ problem_id: problemId })
      })
      if (data.all_bookmarks) {
        setUserStats(prev => ({
          ...(prev || {}),
          bookmarks: data.all_bookmarks
        }))
        showToast(data.bookmarked ? 'Problem added to bookmarks' : 'Problem removed from bookmarks')
      }
    } catch {
      setUserStats(prev => {
        const b = prev?.bookmarks || []
        const exists = b.includes(problemId)
        const updated = exists ? b.filter(x => x !== problemId) : [...b, problemId]
        return { ...(prev || {}), bookmarks: updated }
      })
    }
  }

  // Unlock reference solution for 1 VJ Coin
  async function handleUnlockSolution(problemId) {
    try {
      const data = await apiFetchJson(`/api/problems/${problemId}/unlock-solution`, {
        method: 'POST'
      })
      if (!data.success) {
        showToast(data.error || 'Failed to unlock solution')
        return
      }

      setIsCurrentUnlocked(true)
      if (data.solution) {
        setCurrentSolution(data.solution)
      }

      const updatedCoins = data.coins !== undefined ? data.coins : Math.max(0, (coinBalance ?? 1) - 1)
      setCoinBalance(updatedCoins)
      triggerCoinPulse()

      setUserStats(prev => ({
        ...(prev || {}),
        coins: updatedCoins,
        unlocked_solutions: [...(prev?.unlocked_solutions || []), problemId]
      }))
      showToast(`🔓 Reference Solution Unlocked (-1 VJ Coin)!`)

      // Refresh transactions and balance
      apiFetchJson('/api/user/stats')
        .then(s => setUserStats(s))
        .catch(() => {})
    } catch (err) {
      showToast(err.message || 'Could not complete unlock transaction.')
    }
  }

  // Claim daily streak practice bonus (1 VJ Coin)
  async function handleClaimDailyReward() {
    try {
      const data = await apiFetchJson('/api/account/daily-reward', {
        method: 'POST'
      })

      if (data.awarded) {
        showToast(`🎉 Daily Login Reward: +1 VJ Coin granted! (${data.streak}-day streak)`)
        if (data.coins !== undefined) {
          setCoinBalance(data.coins)
          triggerCoinPulse()
        }
        setUserStats(prev => ({
          ...(prev || {}),
          coins: data.coins !== undefined ? data.coins : (prev?.coins || 0) + 1,
          claimed_today: true,
          streak: data.streak,
          longest_streak: data.longest_streak,
          next_claim_date: data.next_claim_date
        }))
        if (currentUser) {
          setCurrentUser(prev => ({
            ...(prev || {}),
            coins: data.coins !== undefined ? data.coins : (prev?.coins || 0) + 1,
            streak: data.streak,
            claimed_today: true
          }))
        }
      } else if (data.already_claimed) {
        showToast(data.message || 'Daily login reward already claimed for today.')
        setUserStats(prev => ({
          ...(prev || {}),
          claimed_today: true,
          next_claim_date: data.next_claim_date
        }))
      }

      // Refresh full stats in background
      apiFetchJson('/api/user/stats')
        .then(s => setUserStats(s))
        .catch(() => {})

      return data
    } catch (err) {
      const msg = err.message || 'Network error claiming daily reward.'
      showToast(`⚠️ ${msg}`)
      return { error: msg, awarded: false }
    }
  }

  // Load reference solution into editor
  function handleLoadSolutionCode(canonicalCode) {
    if (!canonicalCode || typeof canonicalCode !== 'object') return
    setFiles(canonicalCode)
    const first = Object.keys(canonicalCode)[0]
    if (first) setActiveFileName(first)
    showToast('⚡ Loaded Reference RTL into Editor!')
  }

  // Progressive paid hint unlock handler (-0.5 VJ Coin)
  async function handleUnlockHint(hintIndex) {
    try {
      const data = await unlockPaidHint(currentId, hintIndex)
      if (data.coins !== undefined) {
        setCoinBalance(data.coins)
        triggerCoinPulse()
      }
      setHints(prev => {
        return (prev || []).map(h => {
          if (h.index === hintIndex) {
            return { ...h, is_unlocked: true, text: data.hint_text }
          }
          return h
        })
      })
      apiFetchJson('/api/user/stats').then(s => setUserStats(s)).catch(() => {})
      return data
    } catch (err) {
      showToast(err.message || 'Failed to unlock hint.')
      throw err
    }
  }

  // Navigate to next challenge in sequence
  function handleNextChallenge() {
    const currentIdx = problems.findIndex(p => p.id === currentId)
    const nextP = problems[(currentIdx + 1) % problems.length]
    if (nextP) {
      setCurrentId(nextP.id)
      showToast(`Navigated to: ${nextP.title}`)
    }
  }

  // Execute Non-Coding Submission (MCQ, Predict Output, Rubrics)
  async function executeNonCodingSubmission() {
    setLoading(true)
    setResult(null)
    setError('')

    const payload = {
      problem_id: currentProblem.id,
      choice: selectedChoice,
      choices: selectedChoices,
      answer: currentProblem.type === 'predict_output' ? predictAnswer : rubricAnswer
    }

    try {
      const data = await apiFetchJson(`/api/questions/${currentProblem.id}/submit`, {
        method: 'POST',
        body: JSON.stringify(payload)
      })
      setResult(data)
      setBackendOnline(true)

      if (data.verdict === 'ACCEPTED') {
        if (data.reward_info?.coins_awarded) {
          const awardedCoins = data.reward_info.coins !== undefined ? data.reward_info.coins : ((coinBalance ?? 0) + 1)
          setCoinBalance(awardedCoins)
          triggerCoinPulse()
          showToast(`🏆 Solved ${currentProblem.difficulty} challenge! +1 VJ Coin awarded.`)
        } else {
          showToast(data.message || 'Accepted! Accurate answer.')
        }
        setUserStats(prev => ({
          ...(prev || {}),
          solved_ids: Array.from(new Set([...(prev?.solved_ids || []), currentProblem.id])),
          mistake_ids: (prev?.mistake_ids || []).filter(id => id !== currentProblem.id)
        }))
      } else {
        showToast(data.message || 'Incorrect answer. Check misconception guidance below.')
        setUserStats(prev => ({
          ...(prev || {}),
          mistake_ids: Array.from(new Set([...(prev?.mistake_ids || []), currentProblem.id]))
        }))
      }
      apiFetchJson('/api/user/stats').then(s => setUserStats(s)).catch(() => {})
    } catch (err) {
      setError(err.message || 'Failed to submit answer.')
    } finally {
      setLoading(false)
    }
  }

  // Open Hint modal with architectural hints
  async function handleOpenHint() {
    if (!hints || hints.length === 0) {
      try {
        const loaded = await fetchProblemHints(currentId)
        if (loaded && loaded.length > 0) {
          setHints(loaded)
        }
      } catch (e) {}
    }
    setHintModalOpen(true)
  }

  // Execute simulation (Sample Run or Full Submit)
  async function executeSimulation(mode = 'full', filesOverride = null) {
    setLoading(true)
    setResult(null)
    setError('')
    setTargetWaveformTime(null)

    // Determine files to send, falling back if empty
    let filesToSend = filesOverride || files
    if (!filesToSend || Object.keys(filesToSend).length === 0 || !Object.values(filesToSend).some(c => typeof c === 'string' && c.trim().length > 0)) {
      filesToSend = currentProblem.starter_files || FALLBACK_PROBLEMS[0].starter_files || {}
    }

    const activeCode = filesToSend[activeFileName] || Object.values(filesToSend)[0] || ''

    try {
      const data = await apiFetchJson('/api/submit', {
        method: 'POST',
        body: JSON.stringify({
          problem_id: currentProblem.id,
          language,
          files: filesToSend,
          code: activeCode,
          mode
        })
      })

      setResult(data)
      setBackendOnline(true)

      // Tab routing & solve reward handling based on outcome
      if (data.verdict === 'ACCEPTED') {
        setActiveBottomTab('waveform')

        if (data.reward_info?.coins_awarded) {
          const awardedCoins = data.reward_info.coins !== undefined ? data.reward_info.coins : ((coinBalance ?? 0) + 1)
          setCoinBalance(awardedCoins)
          triggerCoinPulse()
          showToast(`🏆 Solved ${currentProblem.difficulty} challenge! +1 VJ Coin awarded.`)
          setUserStats(prev => ({
            ...(prev || {}),
            coins: awardedCoins,
            solved_ids: Array.from(new Set([...(prev?.solved_ids || []), currentProblem.id]))
          }))
        } else {
          showToast(mode === 'sample' ? 'Sample test cases passed!' : 'Accepted! All test cases passed.')
        }
      } else if (data.diagnostics?.suspected_root_causes?.length > 0 || data.diagnostics?.first_mismatch) {
        setActiveBottomTab('debug')
      } else if (data.test_results?.length > 0) {
        setActiveBottomTab('tests')
      } else {
        setActiveBottomTab('console')
      }

      // Bring results area into view smoothly (or immediate if reduced motion)
      const diagEl = document.getElementById('diagnostics-results-panel')
      if (diagEl) {
        diagEl.scrollIntoView({ behavior: isReducedMotion() ? 'auto' : 'smooth', block: 'nearest' })
      }

      // Refresh history & user stats on full submit
      if (mode === 'full') {
        apiFetchJson(`/api/submissions/${currentId}`)
          .then(recs => setHistory(recs))
          .catch(() => {})

        apiFetchJson('/api/user/stats')
          .then(s => setUserStats(s))
          .catch(() => {})
      }
    } catch (err) {
      setError(err.message || 'Could not connect to HDL Judge backend.')
      setBackendOnline(false)
      const diagEl = document.getElementById('diagnostics-results-panel')
      if (diagEl) {
        diagEl.scrollIntoView({ behavior: isReducedMotion() ? 'auto' : 'smooth', block: 'nearest' })
      }
    } finally {
      setLoading(false)
    }
  }

  // Keyboard shortcut Ctrl+Enter / Cmd+Enter to Submit
  useEffect(() => {
    function handleKeyDown(e) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault()
        executeSimulation('full')
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [files, currentProblem, language])

  // Select problem from catalog or tracks
  function handleSelectProblemAndSwitch(problemId) {
    setCurrentId(problemId)
    setCurrentView('workspace')
  }

  // Jump to waveform with specific timestamp
  function handleJumpToWaveformTime(t) {
    if (t !== null && t !== undefined) {
      setTargetWaveformTime(t)
    }
    setActiveBottomTab('waveform')
  }

  const isBookmarked = userStats?.bookmarks?.includes(currentProblem.id) || false
  const accepted = result?.verdict === 'ACCEPTED'
  const isProblemUnlocked = isCurrentUnlocked || userStats?.unlocked_solutions?.includes(currentProblem.id)

  function handleSelectIde(newIde) {
    setSelectedIde(newIde)
    const validLangs = getLanguagesForIde(newIde)
    if (!validLangs.some(l => l.id === language)) {
      setLanguage(validLangs[0]?.id || 'verilog')
    }
  }

  return (
    <div className="hdl-platform-app">
      {/* Top Navbar: Compact Header with branding, navigation & custom VJ coin balance */}
      <Navbar
        currentView={currentView}
        onChangeView={setCurrentView}
        problems={problems}
        currentProblemId={currentId}
        onSelectProblem={setCurrentId}
        backendOnline={backendOnline}
        onRunSample={() => executeSimulation('sample')}
        onSubmitFull={() => executeSimulation('full')}
        loading={loading}
        canRun={Object.keys(files).length > 0}
        streak={userStats?.streak || 0}
        coins={coinBalance}
        coinLoading={coinLoading}
        coinError={coinError}
        onRetryCoins={() => refreshCoinBalance(false)}
        animateCoins={animateCoins}
        claimedToday={userStats?.claimed_today || false}
        username={currentUser?.username || userStats?.username || 'Engineer'}
        currentUser={currentUser}
        showToast={showToast}
        selectedIde={selectedIde}
        onSelectIde={handleSelectIde}
        language={language}
        onSelectLanguage={setLanguage}
        onOpenStreakModal={() => setStreakModalOpen(true)}
        onClaimDailyReward={handleClaimDailyReward}
        onOpenAuthModal={() => setAuthModalOpen(true)}
        onScrollToDescription={() => {
          const el = document.getElementById('problem-description-section')
          if (el) el.scrollIntoView({ behavior: isReducedMotion() ? 'auto' : 'smooth' })
        }}
      />

      {/* Account / Authentication Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        currentUser={currentUser}
        onUserChanged={handleUserChanged}
        showToast={showToast}
      />

      {/* Streak & Rewards Economy Modal */}
      <StreakRewardsModal
        isOpen={streakModalOpen}
        onClose={() => setStreakModalOpen(false)}
        stats={{ ...(userStats || {}), coins: coinBalance !== null ? coinBalance : (userStats?.coins ?? 0) }}
        onClaimDailyReward={handleClaimDailyReward}
      />

      {/* Progressive Architectural Hints Modal */}
      <HintModal
        isOpen={hintModalOpen}
        onClose={() => setHintModalOpen(false)}
        problem={currentProblem}
        hints={hints}
        progressiveHints={hints}
        coinBalance={coinBalance ?? 0}
        onUnlockHint={handleUnlockHint}
        showToast={showToast}
      />

      {/* Floating Toast Notification (Accessible & Mobile/Desktop Optimized) */}
      {toast && (
        <div
          className={`floating-toast toast-${toast.type || 'info'}`}
          role="status"
          aria-live="polite"
        >
          <div className="toast-content-col">
            <span className="toast-type-tag">
              {toast.type === 'success' ? '✓ SUCCESS' : toast.type === 'error' ? '⚠️ NOTICE' : 'ℹ️ INFO'}
            </span>
            <span className="toast-text">{toast.message}</span>
          </div>
          <button
            type="button"
            className="toast-dismiss-btn"
            onClick={() => setToast(null)}
            aria-label="Dismiss notification"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Page Views */}
      {currentView === 'problems' && (
        <ProblemCatalog
          problems={problems}
          solvedIds={userStats?.solved_ids || []}
          bookmarks={userStats?.bookmarks || []}
          attemptedIds={userStats?.attempted_ids || []}
          mistakeIds={userStats?.mistake_ids || []}
          onSelectProblem={handleSelectProblemAndSwitch}
          onToggleBookmark={handleToggleBookmark}
        />
      )}

      {currentView === 'tracks' && (
        <LearningPaths
          problems={problems}
          solvedIds={userStats?.solved_ids || []}
          onSelectProblem={handleSelectProblemAndSwitch}
        />
      )}

      {currentView === 'dashboard' && (
        <UserDashboard
          stats={{ ...(userStats || {}), coins: coinBalance !== null ? coinBalance : (userStats?.coins ?? 0) }}
          problems={problems}
          onSelectProblem={handleSelectProblemAndSwitch}
          onClaimDailyReward={handleClaimDailyReward}
          onOpenStreakModal={() => setStreakModalOpen(true)}
        />
      )}

      {/* Primary Workspace View: Compact, Single-Column LeetCode/IDE Order */}
      {currentView === 'workspace' && (
        <div className="workspace-main-container">
          {/* 1. Compact Problem Selector Bar: Problem Dropdown + Difficulty + Language + Jump Link */}
          <div className="workspace-quick-bar">
            <div className="quick-bar-left">
              <label htmlFor="quick-prob-select" className="quick-label">Challenge:</label>
              <select
                id="quick-prob-select"
                className="quick-problem-select"
                value={currentId}
                onChange={e => setCurrentId(e.target.value)}
                aria-label="Select Challenge"
              >
                {problems.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.title}
                  </option>
                ))}
              </select>
              <span className={`diff-badge diff-${currentProblem.difficulty?.toLowerCase() || 'easy'}`}>
                {currentProblem.difficulty || 'Easy'}
              </span>
              <button
                className={`quick-bookmark-btn ${isBookmarked ? 'bookmarked' : ''}`}
                onClick={() => handleToggleBookmark(currentProblem.id)}
                title={isBookmarked ? 'Remove bookmark' : 'Bookmark problem'}
                aria-label="Bookmark problem"
              >
                {isBookmarked ? '★' : '☆'}
              </button>
            </div>

            <div className="quick-bar-right">
              {/* IDE Selection Dropdown */}
              <div className="quick-bar-dropdown-cell">
                <label htmlFor="quick-ide-select" className="quick-dropdown-tag">IDE:</label>
                <div className="quick-select-housing">
                  <select
                    id="quick-ide-select"
                    value={selectedIde}
                    onChange={e => handleSelectIde(e.target.value)}
                    className="quick-select-ctrl ide-select-ctrl"
                    title="Simulation & Development Environment"
                    aria-label="Select IDE"
                  >
                    {IDE_ENVIRONMENTS.map(env => (
                      <option key={env.id} value={env.id}>
                        {env.shortName}
                      </option>
                    ))}
                  </select>
                  <span className="quick-arrow-glyph">▾</span>
                </div>
              </div>

              {/* Output Size Dropdown (540, 640, 840) */}
              <div className="quick-bar-dropdown-cell">
                <label htmlFor="quick-size-select" className="quick-dropdown-tag">Size:</label>
                <div className="quick-select-housing">
                  <select
                    id="quick-size-select"
                    value={outputSize}
                    onChange={e => setOutputSize(e.target.value)}
                    className="quick-select-ctrl size-select-ctrl"
                    title="Workspace Output Height Size"
                    aria-label="Select Output Size"
                  >
                    <option value="540">540</option>
                    <option value="640">640</option>
                    <option value="840">840</option>
                  </select>
                  <span className="quick-arrow-glyph">▾</span>
                </div>
              </div>

              {/* Language Selection Dropdown (Language-aware Conditional Rendering) */}
              <div className="quick-bar-dropdown-cell">
                <label htmlFor="quick-lang-select" className="quick-dropdown-tag">Lang:</label>
                <div className="quick-select-housing">
                  <select
                    id="quick-lang-select"
                    value={language}
                    onChange={e => setLanguage(e.target.value)}
                    className="quick-select-ctrl lang-select-ctrl"
                    title="Execution Language for Active IDE"
                    aria-label="Select Language"
                  >
                    {getLanguagesForIde(selectedIde).map(l => (
                      <option key={l.id} value={l.id}>
                        {l.name}
                      </option>
                    ))}
                  </select>
                  <span className="quick-arrow-glyph">▾</span>
                </div>
              </div>

              <button
                className="quick-spec-jump-btn"
                onClick={() => {
                  const el = document.getElementById('problem-description-section')
                  if (el) el.scrollIntoView({ behavior: 'smooth' })
                }}
                title="Jump down to Problem Description and Port Specifications"
              >
                📖 Spec ↓
              </button>
            </div>
          </div>

          {/* 2. Interactive Workspace View: Non-Coding Quiz/Rubrics OR Multi-File Monaco Editor */}
          <div className="workspace-editor-section" id="workspace-editor-section">
            {currentProblem.type === 'single_choice' ? (
              <div className="noncoding-workspace-card">
                <div className="noncoding-card-header">
                  <span className="noncoding-title">🎯 Single-Choice Conceptual Challenge</span>
                  <button className="open-hint-subbtn" onClick={handleOpenHint}>💡 Hints ({hints.length || 2})</button>
                </div>
                <p className="noncoding-desc">{currentProblem.description}</p>
                <div className="options-interactive-grid">
                  {(currentProblem.options || []).map((opt, oIdx) => {
                    const optKey = opt.trim().substring(0, 1).toUpperCase()
                    const isSelected = selectedChoice === optKey
                    return (
                      <div
                        key={oIdx}
                        className={`option-choice-item ${isSelected ? 'selected' : ''}`}
                        onClick={() => setSelectedChoice(optKey)}
                      >
                        <div className="option-radio-indicator" />
                        <span className="option-choice-text">{opt}</span>
                      </div>
                    )
                  })}
                </div>
                <button
                  type="button"
                  className="noncoding-submit-btn"
                  disabled={loading || !selectedChoice}
                  onClick={executeNonCodingSubmission}
                >
                  {loading ? 'Evaluating...' : 'Check Answer ➔'}
                </button>
              </div>
            ) : currentProblem.type === 'multiple_choice' ? (
              <div className="noncoding-workspace-card">
                <div className="noncoding-card-header">
                  <span className="noncoding-title">☑️ Multiple-Choice Selection Challenge</span>
                  <button className="open-hint-subbtn" onClick={handleOpenHint}>💡 Hints</button>
                </div>
                <p className="noncoding-desc">{currentProblem.description}</p>
                <div className="options-interactive-grid">
                  {(currentProblem.options || []).map((opt, oIdx) => {
                    const optKey = opt.trim().substring(0, 1).toUpperCase()
                    const isSelected = selectedChoices.includes(optKey)
                    return (
                      <div
                        key={oIdx}
                        className={`option-choice-item ${isSelected ? 'selected' : ''}`}
                        onClick={() => {
                          setSelectedChoices(prev =>
                            prev.includes(optKey) ? prev.filter(x => x !== optKey) : [...prev, optKey]
                          )
                        }}
                      >
                        <div className="option-radio-indicator" />
                        <span className="option-choice-text">{opt}</span>
                      </div>
                    )
                  })}
                </div>
                <button
                  type="button"
                  className="noncoding-submit-btn"
                  disabled={loading || selectedChoices.length === 0}
                  onClick={executeNonCodingSubmission}
                >
                  {loading ? 'Verifying...' : 'Verify Choices ➔'}
                </button>
              </div>
            ) : currentProblem.type === 'predict_output' ? (
              <div className="noncoding-workspace-card">
                <div className="noncoding-card-header">
                  <span className="noncoding-title">🔮 Predict Simulation Output</span>
                  <button className="open-hint-subbtn" onClick={handleOpenHint}>💡 Hints</button>
                </div>
                <div className="noncoding-desc" style={{ whiteSpace: 'pre-line' }}>{currentProblem.description}</div>
                <div className="predict-output-form">
                  <label htmlFor="predict-input"><strong>Expected Output:</strong></label>
                  <input
                    id="predict-input"
                    type="text"
                    className="predict-input-field"
                    placeholder="e.g. fc or a=5,b=20"
                    value={predictAnswer}
                    onChange={e => setPredictAnswer(e.target.value)}
                  />
                  <button
                    type="button"
                    className="noncoding-submit-btn"
                    disabled={loading || !predictAnswer.trim()}
                    onClick={executeNonCodingSubmission}
                  >
                    {loading ? 'Simulating...' : 'Verify Output ➔'}
                  </button>
                </div>
              </div>
            ) : (currentProblem.type === 'conceptual' || currentProblem.type === 'interview_scenario') ? (
              <div className="noncoding-workspace-card">
                <div className="noncoding-card-header">
                  <span className="noncoding-title">📋 {currentProblem.type === 'interview_scenario' ? 'Principal Interview Scenario' : 'Technical Architectural Concept'}</span>
                  <button className="open-hint-subbtn" onClick={handleOpenHint}>💡 Rubric Guide</button>
                </div>
                <div className="noncoding-desc" style={{ whiteSpace: 'pre-line' }}>{currentProblem.description}</div>

                {currentProblem.rubric_criteria?.length > 0 && (
                  <div className="rubric-criteria-grid">
                    {currentProblem.rubric_criteria.map((crit, cIdx) => (
                      <div key={cIdx} className="rubric-criterion-card">
                        <div className="rubric-crit-title">{crit.criterion} ({crit.points} pts)</div>
                        <p className="rubric-crit-desc">{crit.desc}</p>
                      </div>
                    ))}
                  </div>
                )}

                <textarea
                  className="rubric-textarea"
                  placeholder="Type your technical explanation and architectural breakdown here..."
                  value={rubricAnswer}
                  onChange={e => setRubricAnswer(e.target.value)}
                />

                <button
                  type="button"
                  className="noncoding-submit-btn"
                  disabled={loading || !rubricAnswer.trim()}
                  onClick={executeNonCodingSubmission}
                >
                  {loading ? 'Evaluating Rubric...' : 'Submit Technical Assessment ➔'}
                </button>
              </div>
            ) : (
              <MultiFileEditor
                files={files}
                activeFileName={activeFileName}
                onSelectFile={setActiveFileName}
                onChangeCode={handleChangeCode}
                onResetCode={handleResetCode}
                onSaveDraft={handleSaveDraft}
                selectedIde={selectedIde}
                onSelectIde={handleSelectIde}
                language={language}
                onChangeLanguage={setLanguage}
                outputSize={outputSize}
                onChangeOutputSize={setOutputSize}
                fontSize={fontSize}
                onChangeFontSize={setFontSize}
                onRunSample={filesOverride => executeSimulation('sample', filesOverride)}
                onSubmitFull={filesOverride => executeSimulation('full', filesOverride)}
                onOpenHint={handleOpenHint}
                loading={loading}
                canRun={Object.keys(files).length > 0}
                showToast={showToast}
                onScrollToDescription={() => {
                  const el = document.getElementById('problem-description-section')
                  if (el) el.scrollIntoView({ behavior: 'smooth' })
                }}
              />
            )}
          </div>

          {/* Interactive Learning: Celebration Banner with Suggested Next Challenge */}
          {result?.verdict === 'ACCEPTED' && (
            <div className="celebration-challenge-banner" role="status">
              <div className="celebration-left">
                <span className="celebration-icon" aria-hidden="true">🎉</span>
                <div>
                  <h4>Accepted! Challenge Completed</h4>
                  <p>{result.appreciation || "Outstanding work! You demonstrated complete mastery of this design."}</p>
                </div>
              </div>
              <button
                type="button"
                className="next-challenge-btn"
                onClick={handleNextChallenge}
              >
                Suggested Next Challenge ➔
              </button>
            </div>
          )}

          {/* Interactive Learning: Misconception Guidance & Encouragement Banner */}
          {result?.verdict === 'WRONG_ANSWER' && (result?.misconception_explanation || result?.feedback) && (
            <div className="misconception-guidance-banner" role="status">
              <div className="guidance-header">
                <span className="guidance-icon" aria-hidden="true">💡</span>
                <h5>Encouraging Misconception Guidance</h5>
              </div>
              <p className="guidance-body">
                {result.misconception_explanation || result.feedback}
              </p>
              <div className="guidance-actions">
                <button type="button" className="open-hint-subbtn" onClick={handleOpenHint}>
                  Get Progressive Clue (0.5 VJ)
                </button>
              </div>
            </div>
          )}

          {/* 3. Coherent Verification Results, Test Suite, Waveform & Debug Analysis Panel */}
          <div className={`workspace-results-section bottom-diagnostics-panel height-${bottomHeight}`} id="diagnostics-results-panel">
            {/* Tab Navigation Header with Height Toggle */}
            <div className="bottom-tabs-header">
              <div className="tabs-nav-list">
                <button
                  className={`nav-btn ${activeBottomTab === 'tests' ? 'active' : ''}`}
                  onClick={() => setActiveBottomTab('tests')}
                >
                  🧪 Test Suite
                  {result?.stats && (
                    <span className={`count-badge ${accepted ? 'pass' : 'fail'}`}>
                      {result.stats.passed}/{result.stats.total}
                    </span>
                  )}
                </button>

                <button
                  className={`nav-btn ${activeBottomTab === 'cycles' ? 'active' : ''}`}
                  onClick={() => setActiveBottomTab('cycles')}
                >
                  📋 Cycle Diff ({result?.cycle_logs?.length || 0})
                </button>

                <button
                  className={`nav-btn ${activeBottomTab === 'waveform' ? 'active' : ''}`}
                  onClick={() => setActiveBottomTab('waveform')}
                >
                  📈 Waveform Viewer
                  {result?.waveform ? <span className="live-dot" /> : null}
                </button>

                <button
                  className={`nav-btn ${activeBottomTab === 'debug' ? 'active' : ''}`}
                  onClick={() => setActiveBottomTab('debug')}
                >
                  🔬 Debug Advisor
                </button>

                <button
                  className={`nav-btn ${activeBottomTab === 'console' ? 'active' : ''}`}
                  onClick={() => setActiveBottomTab('console')}
                >
                  🖥️ Simulator Console
                </button>
              </div>

              <div className="tabs-right-actions">
                {result && (
                  <div className={`verdict-tag ${result.verdict.toLowerCase()}`}>
                    <span className="v-label">{result.verdict}</span>
                    <span className="v-msg">{result.message}</span>
                  </div>
                )}

                <div className="panel-height-buttons">
                  <button
                    className="resize-chip"
                    onClick={() => setBottomHeight(h => h === 'expanded' ? 'normal' : 'expanded')}
                    title={bottomHeight === 'expanded' ? 'Restore height' : 'Expand panel'}
                  >
                    {bottomHeight === 'expanded' ? '▾ Normal' : '▴ Expand'}
                  </button>
                </div>
              </div>
            </div>

            {/* Bottom Body Content */}
            <div className="bottom-tabs-body">
              {error && <div className="error-banner">⚠️ {error}</div>}

              {/* 1. Test Suite Tab */}
              {activeBottomTab === 'tests' && (
                <div className="tab-pane-fade">
                  {!result ? (
                    <div className="empty-state-notice">
                      <div className="empty-icon">⚙️</div>
                      <h4>Ready for RTL Verification</h4>
                      <p>Click <strong>▶ Run Code</strong> for sample cases or <strong>🚀 Submit</strong> to test against the full hidden suite.</p>
                    </div>
                  ) : result.test_results?.length > 0 ? (
                    <div className="tests-cards-grid">
                      {result.test_results.map((t, idx) => (
                        <div
                          key={idx}
                          className={`scenario-card ${t.status.toLowerCase()} clickable`}
                          onClick={() => handleJumpToWaveformTime(t.time_ns)}
                          title="Click to view waveform at this test's execution timestamp"
                        >
                          <div className="card-top">
                            <span className="t-name">
                              {t.is_hidden ? '🔒' : '👁️'} Scenario #{idx + 1}: {t.name}
                            </span>
                            <span className={`t-badge ${t.status.toLowerCase()}`}>
                              {t.status}
                            </span>
                          </div>
                          <p className="t-detail">{t.detail}</p>
                          <div className="t-card-footer">
                            <span className="t-time-tag">Time: {t.time_ns}ns</span>
                            <span className="t-jump-link">Inspect Waveform ➔</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="console-fallback-card">
                      <pre>{result.message || 'No structured test records emitted.'}</pre>
                    </div>
                  )}
                </div>
              )}

              {/* 2. Cycle-by-Cycle Diff Tab */}
              {activeBottomTab === 'cycles' && (
                <div className="tab-pane-fade">
                  {result?.cycle_logs?.length > 0 ? (
                    <div className="cycles-table-wrapper">
                      <table className="cycles-table">
                        <thead>
                          <tr>
                            <th>Time</th>
                            <th>Inputs & Stimuli</th>
                            <th>Expected Output</th>
                            <th>Actual DUT Output</th>
                            <th>Assertion Verdict</th>
                            <th>Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.cycle_logs.map((c, i) => (
                            <tr
                              key={i}
                              className={`cycle-row ${c.match ? 'cycle-pass' : 'cycle-fail'}`}
                              onClick={() => handleJumpToWaveformTime(c.time_num)}
                            >
                              <td className="mono">{c.time}</td>
                              <td className="mono stimuli">{c.inputs}</td>
                              <td className="mono exp-cell">{c.expected}</td>
                              <td className="mono act-cell">{c.actual}</td>
                              <td>
                                <span className={`match-pill ${c.match ? 'ok' : 'err'}`}>
                                  {c.match ? '✓ MATCH' : '✗ MISMATCH'}
                                </span>
                              </td>
                              <td>
                                <button className="jump-mini-btn" title="Inspect waveform at this cycle">
                                  View ➔
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="empty-sub-hint">Execute verification to view cycle-by-cycle signal assertion tables.</p>
                  )}
                </div>
              )}

              {/* 3. Waveform Trace Tab (ONE Unified 4-Section Viewer) */}
              {activeBottomTab === 'waveform' && (
                <div className="tab-pane-fade">
                  <WaveformViewer
                    vcd={result?.waveform}
                    goldenVcd={result?.golden_waveform}
                    goldenAvailable={result?.golden_available}
                    targetTime={targetWaveformTime}
                    testResults={result?.test_results || []}
                    cycleLogs={result?.cycle_logs || []}
                    verdict={result?.verdict}
                    ports={currentProblem?.ports || []}
                    onJumpToTime={handleJumpToWaveformTime}
                  />
                </div>
              )}

              {/* 4. RTL Debug Advisor Tab */}
              {activeBottomTab === 'debug' && (
                <div className="tab-pane-fade">
                  <DebugAdvisor
                    diagnostics={result?.diagnostics}
                    onJumpToWaveform={handleJumpToWaveformTime}
                  />
                </div>
              )}

              {/* 5. Simulator Console Tab */}
              {activeBottomTab === 'console' && (
                <div className="tab-pane-fade">
                  <div className="terminal-shell">
                    <div className="shell-header">
                      <span>Icarus Verilog (iverilog & vvp) Raw Standard Output / Error</span>
                    </div>
                    <pre className="shell-body">
                      {result?.console || result?.message || 'Simulator console is clean. No output.'}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 4. Problem Description, Port Specifications & Solution (Positioned BELOW IDE & Results) */}
          <div className="workspace-spec-section">
            <SpecPanel
              problem={currentProblem}
              history={history}
              isBookmarked={isBookmarked}
              onToggleBookmark={handleToggleBookmark}
              onRestoreSnapshot={handleRestoreSnapshot}
              onScrollToEditor={() => {
                const el = document.getElementById('workspace-editor-section')
                if (el) el.scrollIntoView({ behavior: 'smooth' })
              }}
              isUnlocked={isProblemUnlocked}
              solution={currentSolution}
              userCoins={coinBalance !== null ? coinBalance : (userStats?.coins ?? 0)}
              currentUserCode={files}
              onUnlockSolution={handleUnlockSolution}
              onLoadSolutionCode={handleLoadSolutionCode}
            />
          </div>
        </div>
      )}
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
