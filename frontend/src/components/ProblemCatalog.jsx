import React, { useState, useMemo } from 'react'

export default function ProblemCatalog({
  problems = [],
  solvedIds = [],
  bookmarks = [],
  attemptedIds = [],
  mistakeIds = [],
  onSelectProblem,
  onToggleBookmark
}) {
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [selectedDifficulty, setSelectedDifficulty] = useState('All')
  const [selectedLanguage, setSelectedLanguage] = useState('All')
  const [selectedType, setSelectedType] = useState('All')
  const [statusFilter, setStatusFilter] = useState('all') // 'all' | 'solved' | 'unattempted' | 'attempted' | 'mistakes' | 'bookmarked'

  const categories = useMemo(() => {
    const set = new Set()
    problems.forEach(p => {
      const cat = p.topic || p.category
      if (cat) set.add(cat)
    })
    return ['All', ...Array.from(set).sort()]
  }, [problems])

  const filteredProblems = useMemo(() => {
    return problems.filter(p => {
      // Search
      if (search) {
        const q = search.toLowerCase()
        const matchesTitle = p.title?.toLowerCase().includes(q)
        const matchesId = p.id?.toLowerCase().includes(q)
        const matchesTopic = (p.topic || p.category)?.toLowerCase().includes(q)
        const matchesTags = p.tags?.some(t => t.toLowerCase().includes(q))
        if (!matchesTitle && !matchesId && !matchesTopic && !matchesTags) return false
      }

      // Category
      const pCat = p.topic || p.category
      if (selectedCategory !== 'All' && pCat !== selectedCategory) return false

      // Difficulty
      if (selectedDifficulty !== 'All') {
        const pDiff = (p.difficulty || '').toLowerCase()
        const targetDiff = selectedDifficulty.toLowerCase()
        if (pDiff !== targetDiff) {
          // Normalize Easy/Beginner, Medium/Intermediate, Hard/Advanced
          const diffMap = { easy: 'beginner', medium: 'intermediate', hard: 'advanced' }
          const normP = diffMap[pDiff] || pDiff
          const normTarget = diffMap[targetDiff] || targetDiff
          if (normP !== normTarget) return false
        }
      }

      // Language
      if (selectedLanguage !== 'All') {
        const pLang = (p.language || 'verilog').toLowerCase()
        let targetLang = selectedLanguage.toLowerCase()
        if (targetLang === 'c++') targetLang = 'cpp'
        const normP = pLang === 'c++' ? 'cpp' : pLang
        if (normP !== targetLang) return false
      }

      // Question Type
      if (selectedType !== 'All') {
        const pType = (p.type || 'coding').toLowerCase()
        if (pType !== selectedType.toLowerCase()) return false
      }

      // Status
      const isSolved = solvedIds.includes(p.id) || Boolean(p.is_solved)
      const isBookmarked = bookmarks.includes(p.id) || Boolean(p.is_bookmarked)
      const isAttempted = attemptedIds.includes(p.id) || Boolean(p.is_attempted)
      const isMistake = mistakeIds.includes(p.id) || Boolean(p.is_mistake)

      if (statusFilter === 'solved' && !isSolved) return false
      if (statusFilter === 'unattempted' && isAttempted) return false
      if (statusFilter === 'attempted' && !isAttempted) return false
      if (statusFilter === 'mistakes' && !isMistake) return false
      if (statusFilter === 'bookmarked' && !isBookmarked) return false

      return true
    })
  }, [
    problems, search, selectedCategory, selectedDifficulty, selectedLanguage,
    selectedType, statusFilter, solvedIds, bookmarks, attemptedIds, mistakeIds
  ])

  function formatDifficultyClass(diff) {
    const d = (diff || '').toLowerCase()
    if (d === 'beginner' || d === 'easy') return 'easy'
    if (d === 'intermediate' || d === 'medium') return 'medium'
    if (d === 'advanced' || d === 'hard') return 'hard'
    if (d === 'expert') return 'expert'
    return 'easy'
  }

  function formatTypeLabel(type) {
    switch ((type || '').toLowerCase()) {
      case 'single_choice': return 'MCQ (Single)'
      case 'multiple_choice': return 'MCQ (Multi)'
      case 'predict_output': return 'Predict Output'
      case 'fill_in_code': return 'Fill in Code'
      case 'debugging': return 'Debugging'
      case 'conceptual': return 'Conceptual'
      case 'interview_scenario': return 'Interview Rubric'
      default: return 'Coding RTL'
    }
  }

  function formatLanguageLabel(lang) {
    switch ((lang || '').toLowerCase()) {
      case 'systemverilog': return 'SystemVerilog'
      case 'c': return 'C'
      case 'cpp':
      case 'c++': return 'C++'
      case 'python': return 'Python'
      default: return 'Verilog'
    }
  }

  return (
    <div className="catalog-page-container">
      {/* Header Banner */}
      <div className="catalog-header-banner">
        <div className="banner-content">
          <h2>Hardware & Software Interview Question Library</h2>
          <p>
            Master RTL architecture, CDC protocols, SystemVerilog synthesis, and verification algorithms
            across all 4 difficulty levels and 5 execution languages.
          </p>
        </div>

        <div className="catalog-stats-overview">
          <div className="stat-box" title="Solved challenges">
            <span className="stat-num">{solvedIds.length} / {problems.length}</span>
            <span className="stat-sub">Solved (✓)</span>
          </div>
          <div className="stat-box" title="Questions requiring review">
            <span className="stat-num" style={{ color: mistakeIds.length > 0 ? '#ff7b72' : '#8b949e' }}>
              {mistakeIds.length}
            </span>
            <span className="stat-sub">Mistakes (⚠️)</span>
          </div>
          <div className="stat-box" title="Saved questions">
            <span className="stat-num">{bookmarks.length}</span>
            <span className="stat-sub">Bookmarked (★)</span>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="catalog-filters-bar">
        <div className="search-wrap">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="search-input"
            placeholder="Search questions by title, ID, topic, or tags..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        <div className="dropdowns-group">
          {/* Difficulty Filter */}
          <select
            className="filter-select"
            value={selectedDifficulty}
            onChange={e => setSelectedDifficulty(e.target.value)}
            aria-label="Filter by Difficulty"
          >
            <option value="All">All Difficulties</option>
            <option value="Beginner">Beginner</option>
            <option value="Intermediate">Intermediate</option>
            <option value="Advanced">Advanced</option>
            <option value="Expert">Expert</option>
          </select>

          {/* Language Filter */}
          <select
            className="filter-select"
            value={selectedLanguage}
            onChange={e => setSelectedLanguage(e.target.value)}
            aria-label="Filter by Language"
          >
            <option value="All">All Languages</option>
            <option value="verilog">Verilog</option>
            <option value="systemverilog">SystemVerilog</option>
            <option value="c">C</option>
            <option value="cpp">C++</option>
            <option value="python">Python</option>
          </select>

          {/* Question Type Filter */}
          <select
            className="filter-select"
            value={selectedType}
            onChange={e => setSelectedType(e.target.value)}
            aria-label="Filter by Question Type"
          >
            <option value="All">All Question Types</option>
            <option value="coding">Coding Challenge</option>
            <option value="single_choice">Single-Choice MCQ</option>
            <option value="multiple_choice">Multiple-Choice MCQ</option>
            <option value="predict_output">Predict Output</option>
            <option value="debugging">Debugging</option>
            <option value="conceptual">Conceptual Answer</option>
            <option value="interview_scenario">Interview Scenario</option>
          </select>

          {/* Topic/Category Filter */}
          <select
            className="filter-select"
            value={selectedCategory}
            onChange={e => setSelectedCategory(e.target.value)}
            aria-label="Filter by Topic"
          >
            {categories.map(c => (
              <option key={c} value={c}>{c === 'All' ? 'All Topics' : c}</option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            className="filter-select"
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            aria-label="Filter by Status"
          >
            <option value="all">All Status</option>
            <option value="solved">Solved (✓)</option>
            <option value="unattempted">Unattempted</option>
            <option value="attempted">Attempted</option>
            <option value="mistakes">Review Mistakes (⚠️)</option>
            <option value="bookmarked">Bookmarked (★)</option>
          </select>
        </div>
      </div>

      {/* Problems Table */}
      <div className="problems-table-container">
        <table className="problems-table">
          <thead>
            <tr>
              <th className="th-status">Status</th>
              <th className="th-title">Title & Format</th>
              <th className="th-category">Topic</th>
              <th className="th-difficulty">Difficulty</th>
              <th className="th-language">Language</th>
              <th className="th-tags">Topic Tags</th>
              <th className="th-action">Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredProblems.length === 0 ? (
              <tr>
                <td colSpan={7} className="empty-catalog-cell">
                  <p>No interview questions match your selected filters.</p>
                  <button
                    className="clear-filters-btn"
                    onClick={() => {
                      setSearch('')
                      setSelectedCategory('All')
                      setSelectedDifficulty('All')
                      setSelectedLanguage('All')
                      setSelectedType('All')
                      setStatusFilter('all')
                    }}
                  >
                    Clear All Filters
                  </button>
                </td>
              </tr>
            ) : (
              filteredProblems.map(p => {
                const isSolved = solvedIds.includes(p.id) || Boolean(p.is_solved)
                const isBookmarked = bookmarks.includes(p.id) || Boolean(p.is_bookmarked)
                const isMistake = mistakeIds.includes(p.id) || Boolean(p.is_mistake)
                const diffClass = formatDifficultyClass(p.difficulty)

                return (
                  <tr key={p.id} className="problem-row" onClick={() => onSelectProblem(p.id)}>
                    <td className="td-status" onClick={e => e.stopPropagation()}>
                      <button
                        className={`star-btn ${isBookmarked ? 'active' : ''}`}
                        onClick={() => onToggleBookmark(p.id)}
                        title={isBookmarked ? 'Remove bookmark' : 'Bookmark question'}
                      >
                        {isBookmarked ? '★' : '☆'}
                      </button>
                      {isSolved && <span className="check-solved" title="Solved">✓</span>}
                      {isMistake && !isSolved && <span className="badge-mistake" title="Review Mistake">⚠️</span>}
                    </td>

                    <td className="td-title">
                      <div className="problem-name-wrap">
                        <div className="title-row-top">
                          <span className="problem-link">{p.title}</span>
                          <span className={`type-chip type-${p.type || 'coding'}`}>
                            {formatTypeLabel(p.type)}
                          </span>
                        </div>
                        {p.module_name && p.type === 'coding' && (
                          <code className="module-code">{p.module_name}</code>
                        )}
                      </div>
                    </td>

                    <td className="td-category">
                      <span className="category-pill">{p.topic || p.category}</span>
                    </td>

                    <td className="td-difficulty">
                      <span className={`diff-badge diff-${diffClass}`}>
                        {p.difficulty || 'Beginner'}
                      </span>
                    </td>

                    <td className="td-language">
                      <span className={`lang-badge lang-${p.language || 'verilog'}`}>
                        {formatLanguageLabel(p.language)}
                      </span>
                    </td>

                    <td className="td-tags">
                      <div className="tags-flex">
                        {p.tags?.slice(0, 3).map(tag => (
                          <span key={tag} className="tag-chip">{tag}</span>
                        ))}
                      </div>
                    </td>

                    <td className="td-action" onClick={e => e.stopPropagation()}>
                      <button
                        className="solve-btn"
                        onClick={() => onSelectProblem(p.id)}
                      >
                        {isSolved ? 'Review ➔' : 'Practice ➔'}
                      </button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
