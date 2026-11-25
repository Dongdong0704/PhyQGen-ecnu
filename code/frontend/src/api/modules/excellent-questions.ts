import request from '@/api'
import type { PrototypeQuestion } from '@/prototype/types'

const API_BASE = '/v1/excellent-questions'

export type ExcellentSort = 'created_at' | 'max_rating'
export type SortOrder = 'asc' | 'desc'

export interface ExcellentQuestion extends Pick<
  PrototypeQuestion,
  'id' | 'user_id' | 'title' | 'content' | 'question_type' | 'grade' |
  'bloom_level' | 'created_at' | 'updated_at' | 'version'
> {
  max_teacher_rating: number
  has_illustration: boolean
}

export interface ExcellentQuestionDetail extends ExcellentQuestion, Pick<
  PrototypeQuestion,
  'difficulty' | 'knowledge_point' | 'thinking_tags' | 'answer' | 'explanation' |
  'require_illustration' | 'teacher_status' | 'rating' | 'evidence' |
  'kb_reason' | 'confirmations'
> {
  options?: string | null
  illustration_url?: string | null
}

export interface PaginatedExcellentList {
  items: ExcellentQuestion[]
  total: number
  page: number
  page_size: number
}

export const getExcellentQuestions = (params: {
  page?: number
  page_size?: number
  keyword?: string
  sort_by?: ExcellentSort
  sort_order?: SortOrder
}) => {
  return request.get<PaginatedExcellentList>(`${API_BASE}/list`, { params })
}

export function getExcellentQuestion(id: number) {
  return request.get<ExcellentQuestionDetail>(`${API_BASE}/${id}`)
}
