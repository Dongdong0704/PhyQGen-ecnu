// Recover common unmarked physics notation before Markdown interprets * and _.
const spacing = '[ \\t]*'
const variableLetters = 'A-Za-zα-ωΑ-Ωϕϑ'
const identifierCharacter = '[' + variableLetters + '\\d]'
const identifierEnd =
  '(?!' + identifierCharacter + '|_' + identifierCharacter + ')'
const number = String.raw`(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+\-−]?\d{1,3})?`
const superscript = '[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+'
const power = String.raw`(?:\^(?:\{[+\-−]?\d{1,3}\}|[+\-−]?\d{1,3})|${superscript})`
const subscriptValue =
  '(?:min|max|avg|rms|net|in|out|eq|ref|total|[A-Za-zα-ωΑ-Ω]|\\d{1,4})'
const subscript = String.raw`_(?:\{${subscriptValue}\}|${subscriptValue})`

const unitSymbol =
  '(?:km|cm|mm|[µμ]m|nm|m|ms|[µμ]s|min|s|h|kg|mg|g|kN|N|kJ|J|kW|W|MPa|kPa|Pa|kV|mV|V|mA|A|kΩ|Ω|kHz|MHz|Hz|mT|T|mC|[µμ]C|C|rad|°C|°)'
const unitBase = String.raw`${unitSymbol}(?:${power})?${identifierEnd}`
const units = String.raw`${unitBase}(?:${spacing}[/·⋅]${spacing}${unitBase})*`
const numericValue = String.raw`${number}(?:${power})?`
const measurement = String.raw`${numericValue}${spacing}${units}`
const symbol = String.raw`[${variableLetters}]{1,3}(?:${subscript})?(?:${power})?${identifierEnd}`
const relation = String.raw`(?:<=|>=|<(?!-|[A-Za-z][\w:-]*(?:[ \t]+[^>\r\n]*)?\/?>)|[=≈≤≥>])`
const star = String.raw`(?:(?<![ \t*])\*(?![ \t*])|(?<=[ \t])\*(?=[ \t]))`
const operator = String.raw`(?:[+\-−/×·⋅÷]|${star})`
const variable = String.raw`[${variableLetters}](?:${subscript})?(?:${power})?${identifierEnd}`
const equationSubject = new RegExp(String.raw`^(?:${variable}|${measurement})`)
const comparison = new RegExp(String.raw`${spacing}${relation}${spacing}`, 'y')
const arithmeticOperator = new RegExp(
  String.raw`${spacing}${operator}${spacing}`,
  'y',
)
const atom = new RegExp(
  String.raw`[+\-−]?(?:${numericValue}(?:${spacing}${units})?${identifierEnd}|${symbol})`,
  'y',
)
const openGroup = /[+\-−]?\([ \t]*/y
const closeGroup = new RegExp(String.raw`${spacing}\)(?:${power})?`, 'y')
const singleSymbolEquality = new RegExp(
  String.raw`^[${variableLetters}]${spacing}=${spacing}[${variableLetters}]$`,
)
const quantity = new RegExp('^' + measurement)
const unit = new RegExp('^' + units)
const scriptedVariable = new RegExp(
  String.raw`^[${variableLetters}](?:${subscript}(?:${power})?|${power})${identifierEnd}`,
)
const quantityParts = new RegExp(
  String.raw`(${numericValue})${spacing}(${units})`,
  'g',
)
const subscriptParts = new RegExp(subscript, 'g')
const normalizedPowers = new RegExp(superscript, 'g')
const mathEvidence = /[\d_^+\-−*/×÷·⋅()⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]/
const unitPowers = /[\^⁰¹²³⁴⁵⁶⁷⁸⁹]/
const precedingIdentifier = /[A-Za-z\d_α-ωΑ-Ω.@/#?&=\\]/

const superscripts: Record<string, string> = {
  '⁰': '0',
  '¹': '1',
  '²': '2',
  '³': '3',
  '⁴': '4',
  '⁵': '5',
  '⁶': '6',
  '⁷': '7',
  '⁸': '8',
  '⁹': '9',
  '⁺': '+',
  '⁻': '-',
}

function matchEnd(
  pattern: RegExp,
  value: string,
  start: number,
): number | undefined {
  pattern.lastIndex = start
  return pattern.test(value) ? pattern.lastIndex : undefined
}

function readOperand(
  value: string,
  start: number,
  depth: number,
): number | undefined {
  const inside = matchEnd(openGroup, value, start)
  if (inside === undefined) return matchEnd(atom, value, start)
  if (depth === 4) return
  const end = readArithmetic(value, inside, depth + 1)
  if (end !== undefined) return matchEnd(closeGroup, value, end)
}

function readArithmetic(value: string, start: number, depth: number) {
  let end = readOperand(value, start, depth)
  while (end !== undefined) {
    const next = matchEnd(arithmeticOperator, value, end)
    if (next === undefined) break
    const operandEnd = readOperand(value, next, depth)
    if (operandEnd === undefined) break
    end = operandEnd
  }
  return end
}

function readEquation(value: string) {
  const left = equationSubject.exec(value)?.[0]
  if (!left) return
  let end = left.length
  for (;;) {
    const next = matchEnd(comparison, value, end)
    if (next === undefined) break
    const operandEnd = readArithmetic(value, next, 0)
    if (operandEnd === undefined) break
    end = operandEnd
  }
  if (end > left.length && value[end] !== '^') return value.slice(0, end)
}

function emphasisEnd(source: string, index: number): number | undefined {
  const lineStart = source.lastIndexOf('\n', index - 1) + 1
  if (!source.slice(lineStart, index).includes('*')) return
  const nextLine = source.indexOf('\n', index)
  const line = source.slice(lineStart, nextLine < 0 ? undefined : nextLine)
  // Numeric products cannot open emphasis, but a star before a clause can.
  const emphasis = /(?<![A-Za-z\d_\\*])\*(?![\s*])[^*]*(?<![\s\\*])\*(?!\*)/g
  for (const match of line.matchAll(emphasis)) {
    const open = lineStart + (match.index ?? 0)
    const close = open + match[0].length - 1
    if (open < index && index < close) return close
  }
}

function normalizeMath(value: string) {
  return value
    .replace(subscriptParts, (match) => {
      const label = match.slice(1).replace(/^\{|\}$/g, '')
      return label.length > 1 && /^[A-Za-z]+$/.test(label)
        ? '_{\\mathrm{' + label + '}}'
        : '_{' + label + '}'
    })
    .replace(
      normalizedPowers,
      (match) =>
        '^{' + Array.from(match, (char) => superscripts[char]).join('') + '}',
    )
    .replace(/\^([+\-−]?\d+)/g, '^{$1}')
    .replace(/(\d+(?:\.\d+)?|\.\d+)[eE]([+\-−]?\d{1,3})/g, '$1\\times 10^{$2}')
    .replace(/−/g, '-')
    .replace(/[*×]/g, '\\times ')
    .replace(/[·⋅]/g, '\\cdot ')
    .replace(/÷/g, '\\div ')
    .replace(/≈/g, '\\approx ')
    .replace(/<=|≤/g, '\\le ')
    .replace(/>=|≥/g, '\\ge ')
}

function formatWithUnits(value: string) {
  return normalizeMath(
    value.replace(
      quantityParts,
      (_, amount: string, unitText: string) =>
        amount + '\\,\\mathrm{' + unitText + '}',
    ),
  )
}

export function readPlainPhysicsMath(source: string, index: number) {
  const previous = source[index - 1]
  if (previous === '_') {
    const start = source[index - 2] === '_' ? index - 3 : index - 2
    if (start >= 0 && precedingIdentifier.test(source[start])) return
  } else if (previous && precedingIdentifier.test(previous)) {
    return
  }
  const tail = source.slice(index)
  let equality = readEquation(tail)
  if (equality?.includes('*')) {
    const limit = emphasisEnd(source, index)
    if (limit !== undefined && limit < index + equality.length) {
      equality = readEquation(source.slice(index, limit))
    }
  }
  if (
    equality &&
    (mathEvidence.test(equality) || singleSymbolEquality.test(equality))
  ) {
    return { raw: equality, text: formatWithUnits(equality), display: false }
  }

  const measured = quantity.exec(tail)?.[0]
  if (measured)
    return { raw: measured, text: formatWithUnits(measured), display: false }

  const unitText = unit.exec(tail)?.[0]
  if (unitText && unitPowers.test(unitText)) {
    return {
      raw: unitText,
      text: normalizeMath('\\mathrm{' + unitText + '}'),
      display: false,
    }
  }

  const variableText = scriptedVariable.exec(tail)?.[0]
  if (variableText)
    return {
      raw: variableText,
      text: normalizeMath(variableText),
      display: false,
    }
}
