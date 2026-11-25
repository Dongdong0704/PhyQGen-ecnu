import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { http } from '@/api/http'

interface User {
  id: number
  username: string
  email: string
  role: string
  avatarUrl?: string
}

export const useUserStore = defineStore('user', () => {
  const storedUser = localStorage.getItem('phyqgen.user_info')
  let initialUser: User | null = null
  try {
    initialUser = storedUser ? JSON.parse(storedUser) : null
  } catch {
    localStorage.removeItem('phyqgen.user_info')
  }
  const user = ref<User | null>(initialUser)
  const savedToken = localStorage.getItem('phyqgen.token') || ''
  const token = ref<string>(savedToken)

  const isLoggedIn = computed(() => !!token.value)

  function setUser(userData: User) {
    user.value = userData
    localStorage.setItem('phyqgen.user_info', JSON.stringify(userData))
    localStorage.setItem('phyqgen.userRole', userData.role)
  }

  function setToken(newToken: string) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem('phyqgen.token', newToken)
    } else {
      localStorage.removeItem('phyqgen.token')
    }
  }

  function logout() {
    if (token.value) void http('/v1/auth/logout', { method: 'POST' }).catch(() => {})
    user.value = null
    localStorage.removeItem('phyqgen.user_info')
    localStorage.removeItem('phyqgen.userRole')
    setToken('')
  }

  return {
    user,
    token,
    isLoggedIn,
    setUser,
    setToken,
    logout,
  }
})
