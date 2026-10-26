import { marked } from 'marked'
import katex from 'katex'

const escape = (text: string) =>
  text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
function safeUrl(url: string, image = false): string {
  const value = url.trim()
  if (/^(https?:\/\/|\/[^/]|\.?\.?\/)/i.test(value)) return escape(value)
  if (image && /^data:image\/(png|jpeg|webp|gif);base64,/i.test(value))
    return escape(value)
  return ''
}
/** Render Markdown and math from editable question content without executing raw HTML. */
export function parseMarkdown(markdown: string): string {
  if (!markdown) return ''
  const formulas: { latex: string; block: boolean }[] = []
  const remember = (latex: string, block: boolean) => {
    formulas.push({ latex, block })
    return `PHYQMATH${formulas.length - 1}TOKEN`
  }
  const source = markdown
    .replace(/\$\$([\s\S]*?)\$\$/g, (_, latex) => remember(latex, true))
    .replace(/\$([^$\n]+?)\$/g, (_, latex) => remember(latex, false))
  const renderer = new marked.Renderer()
  renderer.html = (html) => escape(html)
  renderer.link = (href, _title, text) => {
    const url = safeUrl(href)
    return url
      ? `<a href="${url}" target="_blank" rel="noopener noreferrer">${text}</a>`
      : text
  }
  renderer.image = (href, _title, text) => {
    const url = safeUrl(href, true)
    return url
      ? `<img src="${url}" alt="${escape(text)}" style="max-width:100%" />`
      : escape(text)
  }
  let html = marked.parse(source, {
    renderer,
    breaks: true,
    async: false,
  }) as string
  formulas.forEach((formula, i) => {
    let rendered: string
    try {
      rendered = katex.renderToString(formula.latex, {
        throwOnError: false,
        displayMode: formula.block,
        strict: false,
        trust: false,
      })
    } catch {
      rendered = escape(formula.latex)
    }
    html = html.split(`PHYQMATH${i}TOKEN`).join(rendered)
  })
  return html
}
