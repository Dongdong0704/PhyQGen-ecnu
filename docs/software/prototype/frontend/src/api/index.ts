/** Local adapter preserves the original API module boundary; no HTTP request is sent. */
import { handlePrototypeRequest } from '@/prototype/legacy-api'
interface RequestConfig {
  url?: string
  method?: string
  params?: Record<string, any>
  data?: any
  headers?: Record<string, string>
}
async function send<T = any>(config: RequestConfig): Promise<T> {
  await new Promise((resolve) => setTimeout(resolve, 100))
  return handlePrototypeRequest(
    config.url || '',
    config.method || 'get',
    config.data,
    config.params || {},
  ) as Promise<T>
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
