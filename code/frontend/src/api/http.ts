export class HttpError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'HttpError'
  }
}

export async function http<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const token = localStorage.getItem('phyqgen.token')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  let response: Response
  try {
    response = await fetch(`/api${path}`, { ...init, headers })
  } catch (error) {
    if (init.signal?.aborted) throw error
    throw new Error('无法连接后端，请检查服务是否已启动')
  }
  const payload = await response.json().catch(() => undefined)
  if (!response.ok || payload === undefined) {
    if (response.status === 401 && token && localStorage.getItem('phyqgen.token') === token) {
      localStorage.removeItem('phyqgen.token')
      localStorage.removeItem('phyqgen.user_info')
      localStorage.removeItem('phyqgen.userRole')
      window.location.replace('/login')
    }
    throw new HttpError(
      response.status,
      typeof payload?.detail === 'string' ? payload.detail : '后端暂不可用，请稍后重试',
    )
  }
  return payload as T
}
