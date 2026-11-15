import React from 'react'

const TRACKS = [
  {
    id: 'fundamentals',
    title: 'RTL Design Fundamentals',
    icon: '⚡',
    difficulty: 'Beginner',
    description: 'Master core combinational logic, multiplexers, priority arbitration, and arithmetic circuits.',
    problem_ids: ['mux4', 'priority_encoder4', 'alu_4bit']
  },
  {
    id: 'sequential',
    title: 'Sequential Logic & Counters',
    icon: '⏱️',
    difficulty: 'Intermediate',
    description: 'Learn synchronous clocked register updates, rollover counters, and multi-cycle latency timing.',
    problem_ids: ['counter4']
  },
  {
    id: 'fsm',
    title: 'Finite State Machine Mastery',
    icon: '🔄',
    difficulty: 'Intermediate',
    description: 'Design robust 3-always block Mealy and Moore FSMs, sequence pattern matchers, and control logic.',
    problem_ids: ['fsm_seq101']
  },
  {
    id: 'fifo_handshake',
    title: 'FIFOs & Handshake Protocols',
    icon: '📦',
    difficulty: 'Advanced',
    description: 'Multi-module FIFO storage, pointer wrap-around tracking, and valid/ready backpressure pipelines.',
    problem_ids: ['sync_fifo', 'valid_ready_pipe']
  },
  {
    id: 'bus_protocols',
    title: 'SoC Bus Protocols (AMBA APB)',
    icon: '🔌',
    difficulty: 'Expert',
    description: 'Implement industry-standard AMBA APB 32-bit memory-mapped peripherals and register decoders.',
    problem_ids: ['apb_slave_gpio']
  }
]

export default function LearningPaths({ problems, solvedIds = [], onSelectProblem }) {
  return (
    <div className="learning-paths-container">
      <div className="paths-header">
        <h2>RTL & VLSI Learning Tracks</h2>
        <p>Curated step-by-step career tracks tailored for digital hardware engineers and verification interview prep.</p>
      </div>

      <div className="tracks-grid">
        {TRACKS.map(track => {
          const trackProblems = problems.filter(p => track.problem_ids.includes(p.id))
          const completedCount = trackProblems.filter(p => solvedIds.includes(p.id)).length
          const percent = trackProblems.length > 0 ? Math.round((completedCount / trackProblems.length) * 100) : 0

          return (
            <div key={track.id} className="track-card">
              <div className="track-header">
                <span className="track-icon">{track.icon}</span>
                <div>
                  <div className="track-top-meta">
                    <span className="track-diff">{track.difficulty}</span>
                    <span className="track-pct">{percent}% Completed</span>
                  </div>
                  <h3>{track.title}</h3>
                </div>
              </div>

              <p className="track-desc">{track.description}</p>

              {/* Progress Bar */}
              <div className="progress-bar-wrap">
                <div className="progress-fill" style={{ width: `${percent}%` }} />
              </div>

              {/* Step problems */}
              <div className="track-problems-list">
                {trackProblems.map((p, idx) => {
                  const isDone = solvedIds.includes(p.id)
                  return (
                    <div
                      key={p.id}
                      className={`track-step-item ${isDone ? 'done' : ''}`}
                      onClick={() => onSelectProblem(p.id)}
                    >
                      <span className="step-badge">{isDone ? '✓' : idx + 1}</span>
                      <div className="step-info">
                        <span className="step-title">{p.title}</span>
                        <span className="step-module"><code>{p.module_name}</code></span>
                      </div>
                      <span className="step-arrow">➔</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
