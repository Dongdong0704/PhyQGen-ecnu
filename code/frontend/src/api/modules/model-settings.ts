import { http } from '../http'

const path = '/v1/profile/model-settings'

export const modelRoles = [
  { id: 'planner', label: '命题智能体', requiresIllustration: false },
  { id: 'text_reviewer', label: '文本审核智能体', requiresIllustration: false },
  { id: 'illustrator', label: '配图智能体', requiresIllustration: true },
  { id: 'vision_reviewer', label: '图文核验智能体', requiresIllustration: true },
] as const

export type ModelRole = (typeof modelRoles)[number]['id']

export interface AgentModelSettings {
  base_url: string
  model: string
  has_api_key: boolean
  configured: boolean
  inherited?: boolean
}

export interface ModelSettings {
  roles: Record<ModelRole, AgentModelSettings>
  configured: boolean
  illustration_configured: boolean
}

export interface ModelSettingsUpdate {
  base_url: string
  model: string
  api_key?: string
}

export const getModelSettings = (signal?: AbortSignal) =>
  http<ModelSettings>(path, { signal })

export const saveModelSettings = (
  role: ModelRole,
  data: ModelSettingsUpdate,
  signal?: AbortSignal,
) =>
  http<ModelSettings>(`${path}/${role}`, {
    method: 'PUT',
    body: JSON.stringify(data),
    signal,
  })

export const testModelSettings = (
  role: ModelRole,
  data: ModelSettingsUpdate,
  signal?: AbortSignal,
) =>
  http<{ message: string }>(`${path}/${role}/test`, {
    method: 'POST',
    body: JSON.stringify(data),
    signal,
  })

export const deleteModelSettings = (role: ModelRole, signal?: AbortSignal) =>
  http<ModelSettings>(`${path}/${role}`, { method: 'DELETE', signal })
