import request from '@/api'

const API_BASE = '/v1/discussions'

export interface ReplyItem {
  id: number
  question_id: number
  parent_id: number
  user_id: number
  username: string
  role: string
  reply_to_username?: string
  content: string
  created_at: string
}

export interface DiscussionItem {
  id: number
  question_id: number
  parent_id?: number | null
  user_id: number
  username: string
  role: string
  reply_to_username?: string
  content: string
  created_at: string
  replies: ReplyItem[]
}

export interface PaginatedDiscussions {
  items: DiscussionItem[]
  total: number
  page: number
  page_size: number
}

export const getDiscussions = (params: {
  question_id: number
  page?: number
  page_size?: number
}) => {
  return request.get<PaginatedDiscussions>(`${API_BASE}/list`, { params })
}

export const postDiscussion = (data: {
  question_id: number
  user_id: number
  content: string
  parent_id?: number | null
}) => {
  return request.post<DiscussionItem>(`${API_BASE}/post`, data)
}

export const deleteDiscussion = (data: {
  discussion_id: number
  user_id: number
}) => {
  return request.delete<{ success: boolean; message: string }>(
    `${API_BASE}/delete`,
    { data },
  )
}
