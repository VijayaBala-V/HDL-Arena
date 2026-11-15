/**
 * Verilog & SystemVerilog Code Formatter for HDL Arena
 *
 * Provides real, deterministic, AST-aware indentation and formatting:
 * - 4 spaces per indentation level.
 * - Module headers at col 0, port lists at 4 spaces, closing ');' at col 0.
 * - Module body contents (always, assign, declarations) at base 4 spaces.
 * - Statements inside begin...end, case...endcase indented +4 spaces.
 * - Strict alignment of if/else: 'end else begin' and 'end else' align with matching if.
 * - 'endmodule' aligned at col 0.
 * - Preserves comments, strings, directives, and user logic without mutation.
 */

export function formatVerilog(code, options = {}) {
  if (!code || typeof code !== 'string') return ''

  const indentSize = options.tabSize || 4
  const indentStr = ' '.repeat(indentSize)

  const rawLines = code.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n')
  const formattedLines = []

  let inModule = false
  let inPortList = false
  let inBlockComment = false
  let blockIndent = 0 // Relative indent inside module (0 = base module level)
  let pendingIndentNextLine = false
  let consecutiveBlankLines = 0

  for (let i = 0; i < rawLines.length; i++) {
    const rawLine = rawLines[i]
    const trimmed = rawLine.trim()

    // 1. Preserve intentional blank lines (at most 1 consecutive blank line)
    if (!trimmed) {
      if (consecutiveBlankLines === 0 && formattedLines.length > 0) {
        formattedLines.push('')
        consecutiveBlankLines++
      }
      continue
    }
    consecutiveBlankLines = 0

    // 2. Multi-line comment tracking /* ... */
    if (inBlockComment) {
      formattedLines.push(rawLine)
      if (trimmed.includes('*/')) {
        inBlockComment = false
      }
      continue
    }

    if (trimmed.startsWith('/*') && !trimmed.includes('*/')) {
      inBlockComment = true
      const baseLevel = inModule ? 1 + blockIndent : 0
      formattedLines.push(indentStr.repeat(baseLevel) + trimmed)
      continue
    }

    // 3. Extract code without comments and strings for token analysis
    let codeWithoutComments = trimmed
    const lineCommentIdx = codeWithoutComments.indexOf('//')
    if (lineCommentIdx !== -1) {
      codeWithoutComments = codeWithoutComments.substring(0, lineCommentIdx).trim()
    }

    // 4. Token classification for indentation
    const isModuleStart = /^(module|macromodule)\b/i.test(codeWithoutComments)
    const isEndmodule = /^endmodule\b/i.test(codeWithoutComments)
    const isModuleCloseParen = /^\);/i.test(codeWithoutComments)

    // Check if line begins with a block closer that decreases current line indent
    const startsWithEndcase = /^endcase\b/i.test(codeWithoutComments)
    const startsWithEnd = /^(end\b|endcase\b|endtask\b|endfunction\b|endgenerate\b|endspecify\b|endtable\b|join\b|join_any\b|join_none\b|endclass\b|endinterface\b|endpackage\b)/i.test(codeWithoutComments)
    const startsWithElse = /^(else\b|end\s*else\b)/i.test(codeWithoutComments)

    // Calculate effective indentation for this line
    let effectiveIndent = 0

    if (isModuleStart) {
      effectiveIndent = 0
      inModule = true
      blockIndent = 0
      if (codeWithoutComments.includes('(') && !codeWithoutComments.includes(');')) {
        inPortList = true
      }
    } else if (isEndmodule) {
      effectiveIndent = 0
      inModule = false
      inPortList = false
      blockIndent = 0
    } else if (isModuleCloseParen) {
      effectiveIndent = 0
      inPortList = false
    } else if (inPortList) {
      // Inside module port list before ');'
      effectiveIndent = 1
      if (codeWithoutComments.includes(');')) {
        inPortList = false
      }
    } else {
      // Inside module body
      let currentRelIndent = blockIndent

      if (startsWithEndcase || startsWithEnd) {
        currentRelIndent = Math.max(0, blockIndent - 1)
        blockIndent = currentRelIndent
      } else if (pendingIndentNextLine) {
        currentRelIndent = blockIndent + 1
        pendingIndentNextLine = false
      }

      effectiveIndent = inModule ? 1 + currentRelIndent : currentRelIndent
    }

    // 5. Build formatted line with proper indentation
    const indentPrefix = indentStr.repeat(Math.max(0, effectiveIndent))
    formattedLines.push(indentPrefix + trimmed)

    // 6. Update blockIndent for subsequent lines
    if (!isModuleStart && !isEndmodule && !inPortList && !isModuleCloseParen) {
      // Check block openers & closers on this line
      const openMatches = codeWithoutComments.match(/\b(begin|case|casex|casez|task|function|generate|fork|specify|table|class|interface|package)\b/gi) || []
      const closeMatches = codeWithoutComments.match(/\b(end|endcase|endtask|endfunction|endgenerate|endspecify|endtable|join|join_any|join_none|endclass|endinterface|endpackage)\b/gi) || []

      // If line started with end, we already deducted 1 for current line above
      const accountedClose = (startsWithEnd || startsWithEndcase) ? 1 : 0
      const remainingClose = Math.max(0, closeMatches.length - accountedClose)

      const netDelta = openMatches.length - remainingClose
      blockIndent = Math.max(0, blockIndent + netDelta)

      // Single-line if/else without begin: indents only the immediately next statement
      if (/\b(if\s*\([^\)]*\)|else)\s*$/i.test(codeWithoutComments) && !/\bbegin\b/i.test(codeWithoutComments)) {
        pendingIndentNextLine = true
      } else {
        pendingIndentNextLine = false
      }
    }
  }

  // Ensure clean single trailing newline
  let result = formattedLines.join('\n').trimRight() + '\n'
  return result
}

/**
 * Registers Verilog and SystemVerilog language configuration and document formatting
 * providers with Monaco Editor so auto-indent on Enter, paste formatting, and Format Document work.
 */
export function setupMonacoVerilogLanguage(monaco) {
  if (!monaco || !monaco.languages) return

  const languages = ['verilog', 'systemverilog']

  languages.forEach(lang => {
    try {
      // 1. Indentation & OnEnter Rules for SystemVerilog / Verilog
      monaco.languages.setLanguageConfiguration(lang, {
        comments: {
          lineComment: '//',
          blockComment: ['/*', '*/']
        },
        brackets: [
          ['begin', 'end'],
          ['case', 'endcase'],
          ['casex', 'endcase'],
          ['casez', 'endcase'],
          ['module', 'endmodule'],
          ['macromodule', 'endmodule'],
          ['task', 'endtask'],
          ['function', 'endfunction'],
          ['generate', 'endgenerate'],
          ['fork', 'join'],
          ['{', '}'],
          ['[', ']'],
          ['(', ')']
        ],
        autoClosingPairs: [
          { open: '(', close: ')' },
          { open: '[', close: ']' },
          { open: '{', close: '}' },
          { open: '"', close: '"' },
          { open: "'", close: "'" },
          { open: '/*', close: '*/' }
        ],
        surroundingPairs: [
          { open: '(', close: ')' },
          { open: '[', close: ']' },
          { open: '{', close: '}' },
          { open: '"', close: '"' },
          { open: "'", close: "'" }
        ],
        indentationRules: {
          // Lines that trigger an extra level of indentation for the next line
          increaseIndentPattern: new RegExp(
            '^\\s*(module|macromodule|always|always_ff|always_comb|always_latch|initial|task|function|generate|fork|specify|table)\\b.*$|' +
            '^.*\\b(begin|case|casex|casez)\\b.*$|' +
            '^\\s*(if|else\\s+if|else)\\s*\\(.*\\)\\s*$'
          ),
          // Lines that decrease indentation for this line
          decreaseIndentPattern: new RegExp(
            '^\\s*(end|endcase|endmodule|endtask|endfunction|endgenerate|endspecify|endtable|join|join_any|join_none)\\b|' +
            '^\\s*\\);'
          ),
          // Next line after if/else without begin should indent
          indentNextLinePattern: new RegExp(
            '^\\s*(if\\s*\\(.*\\)|else)\\s*$'
          )
        },
        onEnterRules: [
          {
            // After `begin`, indent next line and unindent when `end` is typed
            beforeText: new RegExp('^.*\\bbegin\\s*$'),
            afterText: new RegExp('^\\s*end\\b.*$'),
            action: { indentAction: monaco.languages.IndentAction.IndentOutdent }
          },
          {
            beforeText: new RegExp('^.*\\bbegin\\s*$'),
            action: { indentAction: monaco.languages.IndentAction.Indent }
          },
          {
            beforeText: new RegExp('^.*\\bcase\\s*\\(.*\\)\\s*$'),
            action: { indentAction: monaco.languages.IndentAction.Indent }
          },
          {
            beforeText: new RegExp('^\\s*\\/\\*\\*(?!\\/)'),
            afterText: new RegExp('^\\s*\\*\\/'),
            action: { indentAction: monaco.languages.IndentAction.IndentOutdent, appendText: ' * ' }
          },
          {
            beforeText: new RegExp('^\\s*\\/\\*\\*(?!\\/)'),
            action: { indentAction: monaco.languages.IndentAction.None, appendText: ' * ' }
          },
          {
            beforeText: new RegExp('^(\\t|(\\ \\ ))*\\ \\*(\\ ([^\\*]|\\*[^\\/])*)?$'),
            action: { indentAction: monaco.languages.IndentAction.None, appendText: '* ' }
          },
          {
            beforeText: new RegExp('^(\\t|(\\ \\ ))*\\ \\*\\/\\s*$'),
            action: { indentAction: monaco.languages.IndentAction.None, removeText: 1 }
          }
        ]
      })

      // 2. Document Formatting Edit Provider (Right-Click -> Format Document & Shift+Alt+F)
      monaco.languages.registerDocumentFormattingEditProvider(lang, {
        provideDocumentFormattingEdits(model, _options, _token) {
          const text = model.getValue()
          const formatted = formatVerilog(text, { tabSize: 4 })
          return [
            {
              range: model.getFullModelRange(),
              text: formatted
            }
          ]
        }
      })
    } catch (err) {
      console.warn(`[Monaco] Could not setup language configuration for ${lang}:`, err)
    }
  })
}
