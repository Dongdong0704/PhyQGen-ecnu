export function downloadText(text: string, filename: string) {
  const url = URL.createObjectURL(
    new Blob(['\uFEFF', text], { type: 'text/plain;charset=utf-8' }),
  )
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1500)
}
