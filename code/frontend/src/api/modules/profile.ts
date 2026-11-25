import request from '@/api'

const API_BASE = '/v1/profile'

export interface UserProfile {
  id: number
  username: string
  email?: string
  avatar_url?: string
  role: string
  created_at: string
}

export interface UserPreference {
  theme: string
  language: string
  default_difficulty?: string
  default_question_type?: string
  email_notifications: boolean
}

export interface LoginLog {
  id: number
  ip_address?: string
  user_agent?: string
  login_status: string
  login_time: string
  logout_time?: string
}

export interface ProfileStats {
  total_questions: number
  total_logins: number
  last_login_time?: string
}

export interface UpdateProfileRequest {
  email?: string
  avatar_url?: string
  nickname?: string
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

export interface UpdatePreferenceRequest {
  theme?: string
  language?: string
  default_difficulty?: string
  default_question_type?: string
  email_notifications?: boolean
}

/**
 * 获取用户基本信息
 */
export const getProfileInfo = (params: { user_id: number }) => {
  return request.get<UserProfile>(`${API_BASE}/info`, { params })
}

/**
 * 更新用户基本信息
 */
export const updateProfileInfo = (
  data: UpdateProfileRequest,
  params: { user_id: number },
) => {
  return request.put(`${API_BASE}/info`, data, { params })
}

/**
 * 修改密码
 */
export const changePassword = (
  data: ChangePasswordRequest,
  params: { user_id: number },
) => {
  return request.post(`${API_BASE}/change-password`, data, { params })
}

/**
 * 获取用户偏好设置
 */
export const getPreferences = (params: { user_id: number }) => {
  return request.get<UserPreference>(`${API_BASE}/preferences`, { params })
}

/**
 * 更新用户偏好设置
 */
export const updatePreferences = (
  data: UpdatePreferenceRequest,
  params: { user_id: number },
) => {
  return request.put(`${API_BASE}/preferences`, data, { params })
}

/**
 * 获取登录日志
 */
export const getLoginLogs = (params: {
  user_id: number
  page?: number
  page_size?: number
}) => {
  return request.get<LoginLog[]>(`${API_BASE}/login-logs`, { params })
}

/**
 * 获取个人统计信息
 */
export const getProfileStats = (params: { user_id: number }) => {
  return request.get<ProfileStats>(`${API_BASE}/stats`, { params })
}
