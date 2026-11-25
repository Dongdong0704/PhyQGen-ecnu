import { marked } from 'marked'
import katex from 'katex'
import { readPlainPhysicsMath } from './plain-physics-math'

const escapeHtml = (text: string) =>
  text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')

function safeUrl(url: string, image = false): string {
  const value = url.trim()
  if (/^https?:\/\//i.test(value) || /^\/(?![/\\])/.test(value) || /^\.\.?\//.test(value))
    return escapeHtml(value)
  if (image && /^data:image\/(png|jpeg|webp|gif);base64,/i.test(value))
    return escapeHtml(value)
  return ''
}

// Model output occasionally puts a unit with a math exponent inside \text.
const unitFactor = '[A-Za-zµμΩ°]{1,8}(?:\\s*[\\^_]\\s*(?:\\{\\s*[+-]?\\d+\\s*\\}|[+-]?\\d+))?'
const unitExpression = new RegExp(
  '^(?:[+-]?\\d+(?:\\.\\d+)?\\s*)?' + unitFactor +
  '(?:(?:\\s*(?:[/·⋅]|\\\\(?:cdot|times|,))\\s*|\\s+)' + unitFactor + ')*$',
)

function normalizeUnitNotation(latex: string): string {
  return latex.replace(/\\(?:text|textrm|textnormal)\s*\{((?:[^{}]|\{[^{}]*\})*)\}/g, (original, contents: string) => {
    const unit = contents.trim()
    if (unit.length > 120 || !/[\^_]/.test(unit) || !unitExpression.test(unit))
      return original
    const normalized = unit
      .replace(/([\^_])\s*([+-]?\d+)/g, '$1{$2}')
      .replace(/[·⋅]/g, '\\cdot ')
      .replace(/([\p{L}\d}])\s+(?=\p{L})/gu, '$1\\,')
    return '\\mathrm{' + normalized + '}'
  })
}

const renderFormula = (latex: string, displayMode: boolean) =>
  katex.renderToString(latex, {
    throwOnError: true,
    displayMode,
    strict: false,
    trust: false,
  })

function renderMath({ raw, text, display }: Formula): string {
  try {
    return renderFormula(text, display)
  } catch {
    const normalized = normalizeUnitNotation(text)
    if (normalized !== text) {
      try {
        return renderFormula(normalized, display)
      } catch {
        return escapeHtml(raw)
      }
    }
    return escapeHtml(raw)
  }
}

interface Formula {
  raw: string
  text: string
  display: boolean
}

const mathDelimiters = [
  { open: '$$', close: '$$', display: true },
  { open: '\\[', close: '\\]', display: true },
  { open: '$', close: '$', display: false },
  { open: '\\(', close: '\\)', display: false },
]

function readMath(source: string): Formula | undefined {
  const delimiter = mathDelimiters.find(({ open }) => source.startsWith(open))
  if (!delimiter) return
  const { open, close, display } = delimiter
  let depth = 0
  for (let index = open.length; index < source.length; index++) {
    const char = source[index]
    if (!display && char === '\n') return
    if (depth === 0 && source.startsWith(close, index)) {
      const text = source.slice(open.length, index).trim()
      if (text) return { raw: source.slice(0, index + close.length), text, display }
      return
    }
    if (char === '\\') {
      if (!display && source[index + 1] === '\n') return
      const verb = /^\\verb\*?([^A-Za-z\s])/.exec(source.slice(index))
      if (verb) {
        const end = source.indexOf(verb[1], index + verb[0].length)
        if (end < 0 || source.slice(index, end).includes('\n')) return
        index = end
      } else {
        index++
      }
    } else if (char === '%') {
      if (!display) return
      index = source.indexOf('\n', index)
      if (index < 0) return
    } else if (char === '{') {
      depth++
    } else if (char === '}' && depth) {
      depth--
    }
  }
}

function skipCode(source: string, index: number, marker: string): number {
  const start = index + marker.length
  const lineStart = source.lastIndexOf('\n', index - 1) + 1
  const nextLine = source.indexOf('\n', start)
  const tail = source.slice(start, nextLine < 0 ? undefined : nextLine)
  const atFence = marker.length >= 3 &&
    /^ {0,3}$/.test(source.slice(lineStart, index)) &&
    (marker[0] === '~' || !tail.includes('\x60'))
  if (atFence) {
    if (nextLine < 0) return source.length
    const end = new RegExp('^ {0,3}' + marker[0] + '{' + marker.length + ',}[ \\t]*(?:\\n|$)', 'gm')
    end.lastIndex = nextLine + 1
    return end.test(source) ? end.lastIndex : source.length
  }
  if (marker[0] === '~') return start
  const end = new RegExp('(?<!\\x60)' + marker + '(?!\\x60)', 'g')
  end.lastIndex = start
  const match = end.exec(source)
  return match && !/\n[ \t]*\n/.test(source.slice(start, match.index)) ? end.lastIndex : start
}

function skipLinkTarget(source: string, labelEnd: number): number {
  const start = labelEnd + 2
  const labelStart = source.lastIndexOf('[', labelEnd)
  if (labelStart < 0 || labelStart < source.lastIndexOf('\n', labelEnd) ||
      labelStart < source.lastIndexOf(']', labelEnd - 1)) return start

  let depth = 1
  for (let index = start; index < source.length && source[index] !== '\n'; index++) {
    if (source[index] === '\\') {
      index++
    } else if (source[index] === '(') {
      depth++
    } else if (source[index] === ')') {
      depth--
      if (depth === 0) return index + 1
    }
  }
  return start
}

/** Render Markdown and math from editable question content without executing raw HTML. */
export function parseMarkdown(markdown: string): string {
  if (!markdown) return ''
  const source = markdown.replace(/\r\n?/g, '\n')
  // Protect formulas before Markdown splits table cells and emphasis.
  let prefix = 'PHYQMATH'
  while (source.includes(prefix)) prefix += 'X'
  const markers =
    /\x60+|~{3,}|\$\$?|\\[\s\S]|\]\(|<(?:https?:\/\/|mailto:)[^>\r\n]+>|<\/?[A-Za-z][\w:-]*(?:[ \t]+[^>\r\n]*)?\/?>|\b(?:https?:\/\/|www\.)[^\s<>，。；、！？）】]+|[A-Za-zα-ωΑ-Ωϕϑ\d.]/gi
  const formulas: Formula[] = []
  const parts: string[] = []
  let cursor = 0
  for (let match = markers.exec(source); match; match = markers.exec(source)) {
    const marker = match[0]
    if (/^[\x60~]/.test(marker)) {
      markers.lastIndex = skipCode(source, match.index, marker)
      continue
    }
    if (marker === '](') {
      markers.lastIndex = skipLinkTarget(source, match.index)
      continue
    }
    if (marker[0] === '<' || /^(?:https?:\/\/|www\.)/i.test(marker)) continue
    const formula = marker[0] === '$' || marker === '\\(' || marker === '\\['
      ? readMath(source.slice(match.index))
      : readPlainPhysicsMath(source, match.index)
    if (!formula) continue
    parts.push(source.slice(cursor, match.index), prefix + formulas.length + 'TOKEN')
    formulas.push(formula)
    cursor = markers.lastIndex = match.index + formula.raw.length
  }
  parts.push(source.slice(cursor))

  const placeholders = new RegExp(prefix + '(\\d+)TOKEN', 'g')
  const restore = (value: string, transform: (formula: Formula) => string) =>
    value.replace(placeholders, (_, index) => transform(formulas[Number(index)]))
  const raw = (formula: Formula) => formula.raw
  const escaped = (formula: Formula) => escapeHtml(formula.raw)
  const renderer = new marked.Renderer()
  const renderCode = renderer.code.bind(renderer)
  renderer.code = (code, language) => renderCode(restore(code, raw), restore(language || '', raw), false)
  renderer.codespan = (text) => '<code>' + restore(text, escaped) + '</code>'
  renderer.text = (text) => restore(text, renderMath)
  renderer.html = (html) => escapeHtml(restore(html, raw))
  renderer.link = (href, _title, text) => {
    const url = safeUrl(restore(href, raw))
    return url
      ? '<a href="' + url + '" target="_blank" rel="noopener noreferrer">' + text + '</a>'
      : text
  }
  renderer.image = (href, _title, text) => {
    const url = safeUrl(restore(href, raw), true)
    const alt = escapeHtml(restore(text, raw))
    return url
      ? '<img src="' + url + '" alt="' + alt + '" style="max-width:100%" />'
      : alt
  }
  return marked.parse(parts.join(''), { renderer, breaks: true, async: false }) as string
}
