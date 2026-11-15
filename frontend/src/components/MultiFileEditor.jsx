import React, { useState, useRef, useEffect } from 'react'
import Editor, { loader } from '@monaco-editor/react'
import * as monaco from 'monaco-editor'
import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'
import { formatVerilog, setupMonacoVerilogLanguage } from '../utils/verilogFormatter'
import { IDE_ENVIRONMENTS, getLanguagesForIde, getIdeForLanguage } from '../data/environments'

// Setup worker environment for Vite so Monaco runs 100% locally and offline
if (typeof window !== 'undefined') {
  window.MonacoEnvironment = {
    getWorker(_workerId, _label) {
      return new editorWorker()
    }
  }
  // Register Verilog & SystemVerilog language configuration and document formatting provider
  try {
    setupMonacoVerilogLanguage(monaco)
  } catch (err) {
    console.warn('[Monaco] Setup error:', err)
  }
}

// Direct Monaco loader to the locally installed bundle instead of external CDN
loader.config({ monaco })

export default function MultiFileEditor({
  files = {},
  activeFileName = '',
  onSelectFile,
  onChangeCode,
  onResetCode,
  onSaveDraft,
  selectedIde: externalIde,
  onSelectIde,
  language = 'verilog',
  onChangeLanguage,
  outputSize: externalSize,
  onChangeOutputSize,
  fontSize = 13,
  onChangeFontSize,
  onRunSample,
  onSubmitFull,
  loading = false,
  canRun = true,
  showToast = () => {},
  onScrollToDescription,
  onOpenHint
}) {
  const [internalIde, setInternalIde] = useState('verilog')
  const [internalSize, setInternalSize] = useState('540')
  const [editorEngine, setEditorEngine] = useState('monaco') // 'monaco' | 'native'
  const [wordWrap, setWordWrap] = useState(false) // Default off for crisp mobile & desktop RTL column alignment
  const [showNewFileModal, setShowNewFileModal] = useState(false)
  const [newFileName, setNewFileName] = useState('')
  const [showRenameModal, setShowRenameModal] = useState(false)
  const [renameTarget, setRenameTarget] = useState('')
  const [renameNewName, setRenameNewName] = useState('')
  const [cursorPos, setCursorPos] = useState({ line: 1, col: 1 })
  const [monacoLoaded, setMonacoLoaded] = useState(false)
  const [monacoTimedOut, setMonacoTimedOut] = useState(false)
  const [justCopied, setJustCopied] = useState(false)
  const [justFormatted, setJustFormatted] = useState(false)
  const [justSaved, setJustSaved] = useState(false)

  // Active IDE and Output Size (supporting both controlled & uncontrolled)
  const activeIde = externalIde || internalIde
  const activeSize = String(externalSize || internalSize)

  function handleIdeChange(newIde) {
    if (onSelectIde) {
      onSelectIde(newIde)
    } else {
      setInternalIde(newIde)
    }
    // Language dependency validation
    const supportedLangs = getLanguagesForIde(newIde)
    if (!supportedLangs.some(l => l.id === language)) {
      const defaultLang = supportedLangs[0]?.id || 'verilog'
      if (onChangeLanguage) onChangeLanguage(defaultLang)
    }
  }

  function handleSizeChange(newSize) {
    if (onChangeOutputSize) {
      onChangeOutputSize(newSize)
    } else {
      setInternalSize(newSize)
    }
  }

  const isReducedMotion = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const textareaRef = useRef(null)
  const gutterRef = useRef(null)
  const editorRef = useRef(null)
  const containerRef = useRef(null)

  // Robust responsive layout observer for Monaco Editor
  useEffect(() => {
    if (!editorRef.current) return
    const handleResize = () => {
      try {
        editorRef.current?.layout()
      } catch (err) {
        // ignore layout errors during unmount
      }
    }
    window.addEventListener('resize', handleResize)

    let observer = null
    if (typeof ResizeObserver !== 'undefined' && containerRef.current) {
      observer = new ResizeObserver(() => {
        handleResize()
      })
      observer.observe(containerRef.current)
    }

    return () => {
      window.removeEventListener('resize', handleResize)
      if (observer) observer.disconnect()
    }
  }, [monacoLoaded, activeSize])

  const fileNames = Object.keys(files || {})
  const effectiveActive = activeFileName || fileNames[0] || 'counter4.v'
  const rawCode = files?.[effectiveActive] ?? ''
  // Normalize any literal escaped \n strings to genuine newlines
  const currentCode = typeof rawCode === 'string' ? rawCode.replace(/\\n/g, '\n') : ''

  // Focus textarea when switched to native mode
  useEffect(() => {
    if (editorEngine === 'native' && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [editorEngine, effectiveActive])

  // Watchdog timer for Monaco: if not loaded within 3.5s, offer instant fallback
  useEffect(() => {
    if (editorEngine === 'monaco' && !monacoLoaded) {
      const timer = setTimeout(() => {
        if (!monacoLoaded) {
          setMonacoTimedOut(true)
        }
      }, 3500)
      return () => clearTimeout(timer)
    }
  }, [editorEngine, monacoLoaded])

  // Synchronize gutter scrolling with textarea
  function handleTextareaScroll(e) {
    if (gutterRef.current) {
      gutterRef.current.scrollTop = e.target.scrollTop
    }
    updateCursorPos(e.target)
  }

  function updateCursorPos(el) {
    if (!el) return
    const textBefore = el.value.substring(0, el.selectionStart)
    const lines = textBefore.split('\n')
    const line = lines.length
    const col = lines[lines.length - 1].length + 1
    setCursorPos({ line, col })
  }

  // Smart keyboard handling in native editor: Tab, Auto-indent on Enter, Auto-closing pairs
  function handleTextareaKeyDown(e) {
    const el = e.target
    const { selectionStart, selectionEnd, value } = el

    // Format shortcut: Shift+Alt+F
    if (e.shiftKey && e.altKey && (e.key === 'F' || e.key === 'f')) {
      e.preventDefault()
      handleFormatCode()
      return
    }

    // 1. Tab key -> 4 spaces
    if (e.key === 'Tab') {
      e.preventDefault()
      const newValue = value.substring(0, selectionStart) + '    ' + value.substring(selectionEnd)
      onChangeCode(effectiveActive, newValue)
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = selectionStart + 4
          textareaRef.current.selectionEnd = selectionStart + 4
          updateCursorPos(textareaRef.current)
        }
      }, 0)
      return
    }

    // 2. Enter key -> Smart Auto-Indent
    if (e.key === 'Enter') {
      e.preventDefault()
      const curLine = value.substring(0, selectionStart).split('\n').pop()
      const indentMatch = curLine.match(/^(\s*)/)
      let indent = indentMatch ? indentMatch[1] : ''

      // Extra indent if line ends with begin, case, etc.
      if (/(begin|case|\{|\()\s*$/i.test(curLine.trim())) {
        indent += '    '
      }

      const insertText = '\n' + indent
      const newValue = value.substring(0, selectionStart) + insertText + value.substring(selectionEnd)
      onChangeCode(effectiveActive, newValue)

      setTimeout(() => {
        if (textareaRef.current) {
          const nextPos = selectionStart + insertText.length
          textareaRef.current.selectionStart = nextPos
          textareaRef.current.selectionEnd = nextPos
          updateCursorPos(textareaRef.current)
        }
      }, 0)
      return
    }

    // 3. Auto-closing pairs: (), [], {}, "", ''
    const pairs = { '(': ')', '[': ']', '{': '}', '"': '"', "'": "'" }
    if (pairs[e.key]) {
      e.preventDefault()
      const closeChar = pairs[e.key]
      const newValue = value.substring(0, selectionStart) + e.key + closeChar + value.substring(selectionEnd)
      onChangeCode(effectiveActive, newValue)
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = selectionStart + 1
          textareaRef.current.selectionEnd = selectionStart + 1
          updateCursorPos(textareaRef.current)
        }
      }, 0)
      return
    }

    setTimeout(() => updateCursorPos(el), 0)
  }

  // Copy current active source code to clipboard with reliable fallback
  function handleCopyCode() {
    const textToCopy = currentCode
    setJustCopied(true)
    setTimeout(() => setJustCopied(false), 1400)
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(textToCopy)
        .then(() => showToast(`✓ Copied ${effectiveActive} (${textToCopy.length} chars) to clipboard!`))
        .catch(() => fallbackCopy(textToCopy))
    } else {
      fallbackCopy(textToCopy)
    }
  }

  function fallbackCopy(text) {
    try {
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.position = 'fixed'
      ta.style.left = '-9999px'
      ta.style.top = '0'
      document.body.appendChild(ta)
      ta.focus()
      ta.select()
      const success = document.execCommand('copy')
      document.body.removeChild(ta)
      if (success) {
        showToast(`✓ Copied ${effectiveActive} to clipboard!`)
      } else {
        showToast('Please press Ctrl+C to copy code manually.')
      }
    } catch {
      showToast('Could not access clipboard.')
    }
  }

  // Download active source file (.v or .sv)
  function handleDownloadActiveFile() {
    try {
      const blob = new Blob([currentCode], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = effectiveActive
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      showToast(`✓ Downloaded ${effectiveActive}`)
    } catch {
      showToast('Failed to trigger download.')
    }
  }

  // Download all user project files
  function handleDownloadAllFiles() {
    const keys = Object.keys(files || {})
    if (keys.length === 0) return
    if (keys.length === 1) {
      handleDownloadActiveFile()
      return
    }
    keys.forEach((name, i) => {
      setTimeout(() => {
        const blob = new Blob([files[name]], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = name
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      }, i * 200)
    })
    showToast(`✓ Downloaded ${keys.length} source files!`)
  }

  // Undo / Redo / Find actions
  function handleUndo() {
    if (editorEngine === 'monaco' && editorRef.current) {
      editorRef.current.trigger('toolbar', 'undo')
    } else if (textareaRef.current) {
      document.execCommand('undo')
    }
  }

  function handleRedo() {
    if (editorEngine === 'monaco' && editorRef.current) {
      editorRef.current.trigger('toolbar', 'redo')
    } else if (textareaRef.current) {
      document.execCommand('redo')
    }
  }

  function handleFind() {
    if (editorEngine === 'monaco' && editorRef.current) {
      editorRef.current.getAction('actions.find').run()
    } else if (textareaRef.current) {
      textareaRef.current.focus()
      showToast('Use browser search (Ctrl+F) to find text')
    }
  }

  function handleSelectAll() {
    if (editorEngine === 'monaco' && editorRef.current) {
      editorRef.current.setSelection(editorRef.current.getModel().getFullModelRange())
    } else if (textareaRef.current) {
      textareaRef.current.select()
    }
  }

  // Format Code with deterministic 4-space Verilog indentation
  function handleFormatCode() {
    const latestCode = getLatestCode()
    const formatted = formatVerilog(latestCode, { tabSize: 4 })
    onChangeCode(effectiveActive, formatted)
    if (editorEngine === 'monaco' && editorRef.current) {
      editorRef.current.setValue(formatted)
    }
    setJustFormatted(true)
    setTimeout(() => setJustFormatted(false), 1400)
    showToast(`✨ Formatted ${effectiveActive} (Verilog RTL)`)
  }

  function handleSaveDraftWithFeedback() {
    setJustSaved(true)
    setTimeout(() => setJustSaved(false), 1400)
    if (onSaveDraft) onSaveDraft()
  }

  // File Management: Create, Rename, Delete
  function handleCreateFile(e) {
    e.preventDefault()
    if (!newFileName.trim()) return
    let name = newFileName.trim()
    if (!name.endsWith('.v') && !name.endsWith('.sv')) {
      name += language === 'systemverilog' ? '.sv' : '.v'
    }
    if (!files[name]) {
      const moduleName = name.replace(/\.(v|sv)$/, '')
      const boilerplate = `// Module: ${moduleName}\nmodule ${moduleName}(\n    input  wire clk,\n    input  wire rst\n);\n\n    // Implementation logic\n\nendmodule\n`
      onChangeCode(name, boilerplate)
      onSelectFile(name)
      showToast(`Created new module ${name}`)
    }
    setNewFileName('')
    setShowNewFileModal(false)
  }

  function openRenameModal(name, e) {
    e.stopPropagation()
    setRenameTarget(name)
    setRenameNewName(name)
    setShowRenameModal(true)
  }

  function handleRenameFile(e) {
    e.preventDefault()
    if (!renameNewName.trim() || renameNewName === renameTarget) {
      setShowRenameModal(false)
      return
    }
    let newName = renameNewName.trim()
    if (!newName.endsWith('.v') && !newName.endsWith('.sv')) {
      newName += language === 'systemverilog' ? '.sv' : '.v'
    }
    const updated = { ...files }
    const content = updated[renameTarget]
    delete updated[renameTarget]
    updated[newName] = content
    // Replace whole state
    Object.keys(updated).forEach(k => {
      onChangeCode(k, updated[k])
    })
    onSelectFile(newName)
    setShowRenameModal(false)
    showToast(`Renamed ${renameTarget} to ${newName}`)
  }

  function handleDeleteFile(nameToDelete, e) {
    e.stopPropagation()
    if (fileNames.length <= 1) return
    const remaining = { ...files }
    delete remaining[nameToDelete]
    const nextActive = Object.keys(remaining)[0] || 'counter4.v'
    onSelectFile(nextActive)
    showToast(`Removed ${nameToDelete}`)
  }

  function getLatestCode() {
    if (editorEngine === 'monaco' && editorRef.current) {
      return editorRef.current.getValue()
    }
    if (textareaRef.current) {
      return textareaRef.current.value
    }
    return currentCode
  }

  function handleRun() {
    const latestCode = getLatestCode()
    const updatedFiles = {
      ...files,
      [effectiveActive]: latestCode
    }
    onChangeCode(effectiveActive, latestCode)
    if (onRunSample) {
      onRunSample(updatedFiles)
    }
  }

  function handleSubmit() {
    const latestCode = getLatestCode()
    const updatedFiles = {
      ...files,
      [effectiveActive]: latestCode
    }
    onChangeCode(effectiveActive, latestCode)
    if (onSubmitFull) {
      onSubmitFull(updatedFiles)
    }
  }

  function handleEditorMount(editor) {
    editorRef.current = editor
    setMonacoLoaded(true)
    setMonacoTimedOut(false)
    editor.focus()
  }

  const rawLines = currentCode.split('\n')
  const lineCount = Math.max(25, rawLines.length + 5)

  return (
    <div className="ide-workspace">
      {/* IDE Toolbar Row 1: Source File Tabs & Actions */}
      <div className="ide-toolbar">
        {/* Left: Source File Tabs */}
        <div className="file-tabs-scroll">
          {fileNames.map(name => (
            <div
              key={name}
              className={`file-tab ${name === effectiveActive ? 'active' : ''}`}
              onClick={() => onSelectFile(name)}
              onDoubleClick={e => openRenameModal(name, e)}
              title={`${name} (Double-click to rename)`}
            >
              <span className="file-icon">📄</span>
              <span className="tab-title">{name}</span>
              <button
                className="rename-tab-btn"
                title="Rename module file"
                onClick={e => openRenameModal(name, e)}
              >
                ✎
              </button>
              {fileNames.length > 1 && (
                <button
                  className="close-tab-btn"
                  title="Remove module file"
                  onClick={e => handleDeleteFile(name, e)}
                >
                  ×
                </button>
              )}
            </div>
          ))}

          <button
            className="add-file-btn"
            onClick={() => setShowNewFileModal(true)}
            title="Add new module source file"
          >
            + New File
          </button>
        </div>

        {/* Right: Tools & Execution Controls */}
        <div className="ide-tools-right">
          {/* Quick jump to Problem Spec */}
          {onScrollToDescription && (
            <button
              className="jump-spec-chip"
              onClick={onScrollToDescription}
              title="Jump to problem description & port specifications below"
            >
              📖 Problem Spec ↓
            </button>
          )}

          {/* 1. IDE Selection Dropdown */}
          <div className="compact-control-dropdown-box" title="Select Simulation & Development IDE Environment">
            <label className="compact-dropdown-label" htmlFor="editor-ide-select">IDE:</label>
            <div className="select-dropdown-shell">
              <select
                id="editor-ide-select"
                className="compact-toolbar-select ide-select"
                value={activeIde}
                onChange={e => handleIdeChange(e.target.value)}
                aria-label="Select Development Environment"
              >
                {IDE_ENVIRONMENTS.map(env => (
                  <option key={env.id} value={env.id}>
                    {env.shortName}
                  </option>
                ))}
              </select>
              <span className="select-chevron-arrow">▾</span>
            </div>
          </div>

          {/* 2. Output Size Selection Dropdown (540, 640, 840) */}
          <div className="compact-control-dropdown-box" title="Select Output / Workspace Height Size">
            <label className="compact-dropdown-label" htmlFor="editor-size-select">Size:</label>
            <div className="select-dropdown-shell">
              <select
                id="editor-size-select"
                className="compact-toolbar-select size-select"
                value={activeSize}
                onChange={e => handleSizeChange(e.target.value)}
                aria-label="Select Output Size"
              >
                <option value="540">540</option>
                <option value="640">640</option>
                <option value="840">840</option>
              </select>
              <span className="select-chevron-arrow">▾</span>
            </div>
          </div>

          {/* 3. Programming Language Dropdown (Language-aware Conditional Rendering) */}
          <div className="compact-control-dropdown-box" title="Select Programming Language for Active IDE">
            <label className="compact-dropdown-label" htmlFor="editor-lang-select">Lang:</label>
            <div className="select-dropdown-shell">
              <select
                id="editor-lang-select"
                value={language}
                onChange={e => onChangeLanguage && onChangeLanguage(e.target.value)}
                className="compact-toolbar-select lang-select"
                aria-label="Select Language"
              >
                {getLanguagesForIde(activeIde).map(l => (
                  <option key={l.id} value={l.id}>
                    {l.name}
                  </option>
                ))}
              </select>
              <span className="select-chevron-arrow">▾</span>
            </div>
          </div>

          {/* Editor Engine Chip (Monaco IDE vs Fast Native Text) */}
          <button
            type="button"
            className="compact-engine-toggle-chip"
            onClick={() => setEditorEngine(prev => prev === 'monaco' ? 'native' : 'monaco')}
            title={editorEngine === 'monaco' ? 'Using Monaco Editor (Click for Native Text)' : 'Using Native Text (Click for Monaco)'}
          >
            {editorEngine === 'monaco' ? '⚡ Monaco' : '📝 Text'}
          </button>

          {/* Font Controls */}
          <div className="font-size-controls">
            <button
              className="font-btn"
              onClick={() => onChangeFontSize(Math.max(11, fontSize - 1))}
              title="Decrease Font Size"
            >A-</button>
            <span className="font-size-label">{fontSize}px</span>
            <button
              className="font-btn"
              onClick={() => onChangeFontSize(Math.min(22, fontSize + 1))}
              title="Increase Font Size"
            >A+</button>
          </div>

          {/* Editor Action Buttons */}
          <div className="action-buttons-group">
            <button
              className={`tool-btn copy-btn ${justCopied ? 'active-success' : ''}`}
              onClick={handleCopyCode}
              title="Copy entire active source code to clipboard"
            >
              {justCopied ? '✓ Copied' : '📋 Copy'}
            </button>

            <button
              className="tool-btn download-btn"
              onClick={handleDownloadActiveFile}
              title={`Download ${effectiveActive}`}
            >
              ⬇️ Export
            </button>

            {fileNames.length > 1 && (
              <button
                className="tool-btn download-all-btn"
                onClick={handleDownloadAllFiles}
                title="Download all project source files"
              >
                📦 Export All
              </button>
            )}

            <button
              className="tool-btn undo-btn"
              onClick={handleUndo}
              title="Undo last change (Ctrl+Z)"
            >
              ↶
            </button>

            <button
              className="tool-btn redo-btn"
              onClick={handleRedo}
              title="Redo change (Ctrl+Y)"
            >
              ↷
            </button>

            <button
              className="tool-btn find-btn"
              onClick={handleFind}
              title="Find and replace (Ctrl+F)"
            >
              🔍
            </button>

            <button
              className={`tool-btn format-btn ${justFormatted ? 'active-success' : ''}`}
              onClick={handleFormatCode}
              title="Format Verilog RTL Code (4-space indentation, aligned begin/end/else)"
            >
              {justFormatted ? '✓ Formatted' : '✨ Format'}
            </button>

            <button
              className={`tool-btn wrap-btn ${wordWrap ? 'active' : ''}`}
              onClick={() => setWordWrap(!wordWrap)}
              title={wordWrap ? 'Line Wrapping: ON (Click for Horizontal Panning)' : 'Line Wrapping: OFF (Clean Horizontal Scrolling)'}
            >
              {wordWrap ? 'Wrap: On' : 'Wrap: Off'}
            </button>

            <button
              className={`tool-btn save-btn ${justSaved ? 'active-success' : ''}`}
              onClick={handleSaveDraftWithFeedback}
              title="Save current code draft locally"
            >
              {justSaved ? '✓ Saved' : '💾 Save'}
            </button>

            <button
              className="tool-btn reset-btn"
              onClick={onResetCode}
              title="Reset active file to initial starter template"
            >
              ↺ Reset
            </button>
          </div>

          {/* Integrated Execution Buttons in Toolbar: Hint, Run & Submit grouped together */}
          {(onRunSample || onSubmitFull || onOpenHint) && (
            <div className="toolbar-execution-group">
              {onOpenHint && (
                <button
                  type="button"
                  className="toolbar-hint-btn"
                  onClick={onOpenHint}
                  title="View Architectural & Design Hints"
                >
                  💡 Hint
                </button>
              )}

              {onRunSample && (
                <button
                  type="button"
                  className="toolbar-run-btn"
                  onClick={handleRun}
                  disabled={loading || !canRun}
                  aria-busy={loading}
                  title="Run Visible Sample Test Cases (Ctrl+Enter)"
                >
                  {loading ? '⏳ Running...' : '▶ Run Code'}
                </button>
              )}

              {onSubmitFull && (
                <button
                  type="button"
                  className="toolbar-submit-btn"
                  onClick={handleSubmit}
                  disabled={loading || !canRun}
                  aria-busy={loading}
                  title="Submit RTL to Full Hidden Verification Suite"
                >
                  {loading ? 'Simulating...' : '🚀 Submit'}
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* New File Modal */}
      {showNewFileModal && (
        <div className="modal-backdrop" onClick={() => setShowNewFileModal(false)}>
          <div className="modal-box" onClick={e => e.stopPropagation()}>
            <h4>Create New Module Source File</h4>
            <p className="modal-sub">Enter file name with extension (e.g. <code>submodule.v</code>):</p>
            <form onSubmit={handleCreateFile}>
              <input
                type="text"
                className="modal-input"
                autoFocus
                placeholder="module_name.v"
                value={newFileName}
                onChange={e => setNewFileName(e.target.value)}
              />
              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowNewFileModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-confirm">
                  Create Module
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Rename File Modal */}
      {showRenameModal && (
        <div className="modal-backdrop" onClick={() => setShowRenameModal(false)}>
          <div className="modal-box" onClick={e => e.stopPropagation()}>
            <h4>Rename Source File</h4>
            <p className="modal-sub">Rename <code>{renameTarget}</code> to:</p>
            <form onSubmit={handleRenameFile}>
              <input
                type="text"
                className="modal-input"
                autoFocus
                value={renameNewName}
                onChange={e => setRenameNewName(e.target.value)}
              />
              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowRenameModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-confirm">
                  Save Name
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Fixed and Predictable Editor Dimensions Container */}
      <div ref={containerRef} className={`monaco-container height-${activeSize}`} style={{ height: `${activeSize}px` }}>
        {editorEngine === 'monaco' ? (
          <div className="monaco-wrapper">
            <Editor
              height="100%"
              width="100%"
              language={language === 'c' || language === 'cpp' ? 'cpp' : (language === 'python' ? 'python' : 'systemverilog')}
              theme="vs-dark"
              value={currentCode}
              onMount={handleEditorMount}
              onChange={val => onChangeCode(effectiveActive, val ?? '')}
              loading={
                <div className="monaco-loading-fallback">
                  <span className="spin-fast">⚡</span>
                  <p>Loading Monaco Editor...</p>
                  {monacoTimedOut && (
                    <button
                      type="button"
                      className="switch-now-btn"
                      onClick={() => setEditorEngine('native')}
                    >
                      Switch to Fast Text Editor Mode
                    </button>
                  )}
                </div>
              }
              options={{
                readOnly: false,
                domReadOnly: false,
                accessibilitySupport: 'on',
                mouseStyle: 'text',
                fontSize,
                fontFamily: "'DM Mono', 'Fira Code', Consolas, monospace",
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true,
                tabSize: 4,
                insertSpaces: true,
                detectIndentation: false,
                autoIndent: 'full',
                formatOnPaste: true,
                formatOnType: true,
                renderLineHighlight: 'all',
                cursorBlinking: isReducedMotion ? 'solid' : 'smooth',
                cursorSmoothCaretAnimation: isReducedMotion ? 'off' : 'on',
                smoothScrolling: !isReducedMotion,
                cursorStyle: 'line',
                cursorWidth: 2,
                wordWrap: wordWrap ? 'on' : 'off',
                wrappingIndent: 'indent',
                scrollBeyondLastColumn: 5,
                minimap: { enabled: false },
                padding: { top: 12, bottom: 12 }
              }}
            />
          </div>
        ) : (
          /* Native High-Performance Code Editor with Line Numbers Gutter & 25+ Visible Lines */
          <div className="native-editor-wrapper">
            <div ref={gutterRef} className="native-gutter" style={{ fontSize: `${fontSize}px` }}>
              {Array.from({ length: lineCount }, (_, i) => (
                <span key={i} className={`line-num ${i + 1 === cursorPos.line ? 'active-line' : ''}`}>
                  {i + 1}
                </span>
              ))}
            </div>

            <textarea
              ref={textareaRef}
              className="native-textarea"
              rows={25}
              style={{ fontSize: `${fontSize}px`, minHeight: `${activeSize}px`, height: `${activeSize}px` }}
              value={currentCode}
              onChange={e => {
                onChangeCode(effectiveActive, e.target.value)
                updateCursorPos(e.target)
              }}
              onKeyDown={handleTextareaKeyDown}
              onKeyUp={e => updateCursorPos(e.target)}
              onClick={e => updateCursorPos(e.target)}
              onScroll={handleTextareaScroll}
              placeholder="// Write your Verilog / SystemVerilog RTL implementation here..."
              spellCheck="false"
              autoCapitalize="none"
              autoComplete="off"
              autoCorrect="off"
            />

            <div className="native-statusbar">
              <span>{effectiveActive}</span>
              <span>UTF-8</span>
              <span>Tab: 4 Spaces</span>
              <span>Ln {cursorPos.line}, Col {cursorPos.col}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
