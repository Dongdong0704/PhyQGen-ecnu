/// <reference types="vite/client" />
declare module 'katex' {
  const katex: {
    renderToString(input: string, options?: Record<string, unknown>): string
  }
  export default katex
}
declare module 'element-plus/dist/locale/zh-cn.mjs'
