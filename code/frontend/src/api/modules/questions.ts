import { http } from '@/api/http'
import type { PrototypeQuestion } from '@/prototype/types'

type DraftUpdate = Pick<
  PrototypeQuestion,
  | 'title'
  | 'content'
  | 'options'
  | 'answer'
  | 'explanation'
  | 'illustration_url'
  | 'version'
>

const bankPath = '/v1/questions'

export function listQuestions() {
  return http<PrototypeQuestion[]>(bankPath)
}

export function getQuestion(id: number, signal?: AbortSignal) {
  return http<PrototypeQuestion>(`${bankPath}/${id}`, { signal })
}

export function updateDraft(id: number, update: DraftUpdate) {
  return http<PrototypeQuestion>(`${bankPath}/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(update),
  })
}

export function confirmQuestion(id: number, version: number) {
  return http<PrototypeQuestion>(`${bankPath}/${id}/confirm`, {
    method: 'POST',
    body: JSON.stringify({ version }),
  })
}

export function rateQuestion(id: number, rating: number, comment: string) {
  return http<PrototypeQuestion>(`${bankPath}/${id}/rating`, {
    method: 'POST',
    body: JSON.stringify({ rating, comment }),
  })
}

export function removeQuestion(id: number) {
  return http<void>(`${bankPath}/${id}`, { method: 'DELETE' })
}

export function exportQuestions(ids: number[]) {
  return http<PrototypeQuestion[]>(`${bankPath}/export`, {
    method: 'POST',
    body: JSON.stringify({ ids }),
  })
}
