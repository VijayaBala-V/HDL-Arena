/**
 * Programming Environments & Language Definitions
 * Enforces strict language-aware conditional rendering and state validation.
 */

export const IDE_ENVIRONMENTS = [
  {
    id: 'verilog',
    name: 'Verilog / HDL IDE',
    shortName: 'Verilog IDE',
    badge: 'HDL',
    description: 'Hardware Description & Verification (Icarus Verilog RTL Engine)',
    languages: [
      { id: 'verilog', name: 'Verilog (IEEE 1364)', ext: '.v' },
      { id: 'systemverilog', name: 'SystemVerilog (IEEE 1800)', ext: '.sv' }
    ],
    defaultLanguage: 'verilog'
  },
  {
    id: 'cpp',
    name: 'C / C++ IDE',
    shortName: 'C/C++ IDE',
    badge: 'C++',
    description: 'Embedded Systems & Software-driven Verification Models',
    languages: [
      { id: 'c', name: 'C (Clang C99)', ext: '.c' },
      { id: 'cpp', name: 'C++ (Clang++ C++17)', ext: '.cpp' }
    ],
    defaultLanguage: 'cpp'
  },
  {
    id: 'python',
    name: 'Python IDE',
    shortName: 'Python IDE',
    badge: 'PY',
    description: 'Python Testbench Scripting & Architecture Modeling',
    languages: [
      { id: 'python', name: 'Python 3', ext: '.py' }
    ],
    defaultLanguage: 'python'
  },
  {
    id: 'java',
    name: 'Java IDE',
    shortName: 'Java IDE',
    badge: 'JAVA',
    description: 'JVM-based Hardware Design & Verification Frameworks',
    languages: [
      { id: 'java', name: 'Java (OpenJDK 17)', ext: '.java' }
    ],
    defaultLanguage: 'java'
  }
]

/**
 * Validates whether a language is allowed within an IDE environment.
 */
export function isLanguageSupported(ideId, languageId) {
  const env = IDE_ENVIRONMENTS.find(e => e.id === ideId)
  if (!env) return false
  return env.languages.some(l => l.id === languageId)
}

/**
 * Returns supported languages for a given IDE environment.
 */
export function getLanguagesForIde(ideId) {
  const env = IDE_ENVIRONMENTS.find(e => e.id === ideId)
  return env ? env.languages : IDE_ENVIRONMENTS[0].languages
}

/**
 * Returns the corresponding IDE for a given language.
 */
export function getIdeForLanguage(languageId) {
  const env = IDE_ENVIRONMENTS.find(e => e.languages.some(l => l.id === languageId))
  return env ? env.id : 'verilog'
}
