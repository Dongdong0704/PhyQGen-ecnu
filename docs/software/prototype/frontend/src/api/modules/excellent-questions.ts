import request from '@/api'

const API_BASE = '/v1/excellent-questions'

export interface ExcellentQuestion {
  id: number
  user_id: number
  title: string
  content: string
  question_type: string
  grade: string
  bloom_level: string
  options?: string
  answer: string
  explanation?: string
  illustration_url?: string
  created_at: string
  updated_at: string
  max_teacher_rating: number
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
  sort_by?: string
  sort_order?: string
}) => {
  return request.get<PaginatedExcellentList>(`${API_BASE}/list`, { params })
}
