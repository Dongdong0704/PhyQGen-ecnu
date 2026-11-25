import { http } from '@/api/http'
import type { GenerationParams, GenerationTask } from '@/prototype/types'

const base = '/v1/generation/tasks'

export type GenerationRequest = Omit<GenerationParams, 'scenario'>
export type LiveGenerationTask = Omit<GenerationTask, 'params'> & {
  params: GenerationRequest
}

interface KnowledgeStatus {
  kb_enabled: boolean
  kb_version: string
  kb_status: string
  kb_fragments: number
}

export function startGeneration(
  params: GenerationRequest,
  signal?: AbortSignal,
) {
  return http<LiveGenerationTask>(base, {
    method: 'POST',
    body: JSON.stringify(params),
    signal,
  })
}

export function listGenerationTasks(signal?: AbortSignal) {
  return http<LiveGenerationTask[]>(base, { signal })
}

export function getGenerationTask(id: string, signal?: AbortSignal) {
  return http<LiveGenerationTask>(`${base}/${encodeURIComponent(id)}`, {
    signal,
  })
}

export function getKnowledgeStatus(signal?: AbortSignal) {
  return http<KnowledgeStatus>('/v1/generation/knowledge', { signal })
}
