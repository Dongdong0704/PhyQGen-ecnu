import { http } from './http'
interface RequestConfig {
  url?: string
  method?: string
  params?: Record<string, any>
  data?: any
  headers?: Record<string, string>
}
async function send<T = any>(config: RequestConfig): Promise<T> {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(config.params || {})) {
    if (value !== undefined && value !== null) query.set(key, String(value))
  }
  const path = query.size ? `${config.url}?${query}` : config.url || ''
  return http<T>(path, {
    method: config.method || 'get',
    headers: config.headers,
    body: config.data === undefined ? undefined : JSON.stringify(config.data),
  })
}
const request = Object.assign(send, {
  get: <T = any>(url: string, config: RequestConfig = {}) =>
    send<T>({ ...config, url, method: 'get' }),
  post: <T = any>(url: string, data?: any, config: RequestConfig = {}) =>
    send<T>({ ...config, url, data, method: 'post' }),
  put: <T = any>(url: string, data?: any, config: RequestConfig = {}) =>
    send<T>({ ...config, url, data, method: 'put' }),
  delete: <T = any>(url: string, config: RequestConfig = {}) =>
    send<T>({ ...config, url, method: 'delete' }),
})
export default request
