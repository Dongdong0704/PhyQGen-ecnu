import request from '../index'

export interface LoginParams {
  username: string
  password: string
}

export interface RegisterParams {
  username: string
  email?: string
  password: string
  role?: string
}

export interface AuthResponse {
  code: number
  message: string
  data: {
    access_token: string
    token_type: string
    user: {
      id: number
      username: string
      email?: string
      role: string
    }
  }
}

export const login = (params: LoginParams): Promise<AuthResponse> => {
  return request({
    url: '/v1/auth/login',
    method: 'post',
    data: params,
  })
}

export const register = (params: RegisterParams): Promise<AuthResponse> => {
  return request({
    url: '/v1/auth/register',
    method: 'post',
    data: params,
  })
}
