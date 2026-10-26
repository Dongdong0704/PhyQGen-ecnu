import request from '../index'

export interface User {
  id: number
  username: string
  email?: string
  role: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreateUserParams {
  username: string
  email?: string
  password: string
  role?: string
}

export interface UpdateUserParams {
  username?: string
  email?: string
  role?: string
  is_active?: boolean
}

export interface UpdateUserPasswordParams {
  new_password: string
}

export interface UpdateKeyParams {
  current_password: string
  new_key: string
}

export interface AdminResponse {
  code: number
  message: string
  data: any
}

export const getUsers = (role?: string): Promise<AdminResponse> => {
  return request({
    url: '/v1/admin/users',
    method: 'get',
    params: role ? { role } : {},
  })
}

export const getUser = (userId: number): Promise<AdminResponse> => {
  return request({
    url: `/v1/admin/users/${userId}`,
    method: 'get',
  })
}

export const createUser = (
  params: CreateUserParams,
): Promise<AdminResponse> => {
  return request({
    url: '/v1/admin/users',
    method: 'post',
    data: params,
  })
}

export const updateUser = (
  userId: number,
  params: UpdateUserParams,
): Promise<AdminResponse> => {
  return request({
    url: `/v1/admin/users/${userId}`,
    method: 'put',
    data: params,
  })
}

export const updateUserPassword = (
  userId: number,
  params: UpdateUserPasswordParams,
): Promise<AdminResponse> => {
  return request({
    url: `/v1/admin/users/${userId}/password`,
    method: 'put',
    data: params,
  })
}

export const deleteUser = (userId: number): Promise<AdminResponse> => {
  return request({
    url: `/v1/admin/users/${userId}`,
    method: 'delete',
  })
}

export const verifyRegistrationKey = (key: string): Promise<AdminResponse> => {
  return request({
    url: '/v1/admin/verify-registration-key',
    method: 'post',
    data: { key },
  })
}

export const getRegistrationKey = (): Promise<AdminResponse> => {
  return request({
    url: '/v1/admin/registration-key',
    method: 'get',
  })
}

export const updateRegistrationKey = (
  params: UpdateKeyParams,
): Promise<AdminResponse> => {
  return request({
    url: '/v1/admin/registration-key',
    method: 'put',
    data: params,
  })
}
