import { getCurrentUser } from '@/prototype/store'
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const VALID_ROLES = ['TEACHER', 'ADMIN'] as const

function isValidRole(
  role: string | null,
): role is (typeof VALID_ROLES)[number] {
  return !!role && VALID_ROLES.includes(role as (typeof VALID_ROLES)[number])
}

const routes: Array<RouteRecordRaw> = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/views/dashboard/index.vue'),
    redirect: () => {
      const token = localStorage.getItem('phyqgen.token')
      const userRole = localStorage.getItem('phyqgen.userRole')
      if (token) {
        if (userRole === 'ADMIN') {
          return '/admin/users'
        }
        if (userRole === 'STUDENT' || userRole === 'TEACHER') {
          return '/overview'
        }
        return '/login'
      }
      return '/login'
    },
    meta: { requiresAuth: true, roles: ['TEACHER'] },
    children: [
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('@/views/dashboard/tasks/index.vue'),
        meta: { title: '生成任务' },
      },
      {
        path: 'overview',
        name: 'Overview',
        component: () => import('@/views/dashboard/overview/index.vue'),
        meta: { title: '概览' },
      },
      {
        path: 'question-gen',
        name: 'QuestionGen',
        component: () => import('@/views/dashboard/question-gen/index.vue'),
        meta: { title: '习题生成' },
      },
      {
        path: 'question-bank',
        name: 'QuestionBank',
        component: () => import('@/views/dashboard/question-manage/index.vue'),
        meta: { title: '我的题库' },
      },
      {
        path: 'excellent-questions',
        name: 'ExcellentQuestions',
        component: () =>
          import('@/views/dashboard/excellent-questions/index.vue'),
        meta: { title: '优秀习题' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/dashboard/profile/index.vue'),
        meta: { title: '个人中心' },
      },
    ],
  },
  {
    path: '/admin',
    component: () => import('@/views/admin/index.vue'),
    redirect: '/admin/users',
    meta: { requiresAuth: true, roles: ['ADMIN'] },
    children: [
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/users/index.vue'),
        meta: { title: '用户管理' },
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('@/views/admin/settings/index.vue'),
        meta: { title: '系统维护' },
      },
      {
        path: 'profile',
        name: 'AdminProfile',
        component: () => import('@/views/admin/profile/index.vue'),
        meta: { title: '个人中心' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes: [...routes, { path: '/:pathMatch(.*)*', redirect: '/' }],
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('phyqgen.token')
  const userRole = localStorage.getItem('phyqgen.userRole')
  if (token) {
    try {
      getCurrentUser()
    } catch {
      useUserStore().logout()
      next('/login')
      return
    }
  }

  if (token && !isValidRole(userRole)) {
    localStorage.removeItem('phyqgen.token')
    localStorage.removeItem('phyqgen.userRole')
    localStorage.removeItem('phyqgen.user_info')
    next('/login')
    return
  }

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    if (userRole === 'ADMIN') {
      next('/admin/users')
    } else {
      next('/overview')
    }
  } else if (to.meta.roles && Array.isArray(to.meta.roles)) {
    if (userRole && (to.meta.roles as string[]).includes(userRole)) {
      next()
    } else {
      if (userRole === 'ADMIN') {
        next('/admin/users')
      } else if (userRole === 'STUDENT' || userRole === 'TEACHER') {
        next('/overview')
      } else {
        next('/login')
      }
    }
  } else {
    next()
  }
})

export default router
