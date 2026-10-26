import {
  audit,
  commit,
  getCurrentUser,
  loginLocal,
  prototypeState as state,
  registerLocal,
  requireAdmin,
} from './store'
import type { DemoUser } from './types'
const publicUser = (user: DemoUser) => {
  const { password: _password, ...rest } = user
  return rest
}
const ok = (data: unknown = {}) => ({
  code: 0,
  message: '本地演示操作成功',
  data,
})
const nextId = (items: { id: number }[]) =>
  Math.max(0, ...items.map((i) => i.id)) + 1
const paginate = (items: any[], params: Record<string, any>) => {
  const page = Math.max(1, Number(params.page) || 1),
    page_size = Number(params.page_size) || 10
  return {
    items: items.slice((page - 1) * page_size, page * page_size),
    total: items.length,
    page,
    page_size,
  }
}
export async function handlePrototypeRequest(
  url: string,
  method: string,
  data: any,
  params: Record<string, any>,
): Promise<any> {
  method = method.toLowerCase()
  if (url === '/v1/auth/login' || url === '/v1/auth/register') {
    const user = url.endsWith('login')
      ? loginLocal(data.username, data.password)
      : registerLocal(data)
    return ok({
      access_token: `demo-session-${user.id}`,
      token_type: 'bearer',
      user: publicUser(user),
    })
  }
  const user = getCurrentUser()
  const own = state.questions.filter((q) => q.user_id === user.id)
  if (url === '/v1/overview/stats') {
    const group = (field: string) =>
      own.reduce((a: Record<string, number>, q: any) => {
        const key = q[field] || '未评分'
        a[key] = (a[key] || 0) + 1
        return a
      }, {})
    return {
      total_questions: own.length,
      questions_by_type: group('question_type'),
      questions_by_bloom: group('bloom_level'),
      questions_by_grade: group('grade'),
      questions_by_knowledge: group('knowledge_point'),
      questions_by_rating: group('rating'),
      recent_questions: [...own]
        .sort((a, b) => b.created_at.localeCompare(a.created_at))
        .slice(0, 5),
    }
  }
  if (url === '/v1/overview/trend') return []
  if (url.startsWith('/v1/profile')) {
    if (url.endsWith('/info')) {
      if (method === 'get') return publicUser(user)
      return commit(() => {
        if (data.email !== undefined) user.email = data.email
        if (data.avatar_url !== undefined) user.avatar_url = data.avatar_url
        user.updated_at = new Date().toISOString()
        return ok(publicUser(user))
      })
    }
    if (url.endsWith('/change-password')) {
      if (data.old_password !== user.password) throw new Error('原密码不正确')
      if (data.new_password.length < 6) throw new Error('新密码至少6个字符')
      return commit(() => {
        user.password = data.new_password
        return ok()
      })
    }
    if (url.endsWith('/stats')) {
      const logs = state.loginLogs.filter((l) => l.user_id === user.id)
      return {
        total_questions: own.length,
        total_logins: logs.length,
        last_login_time: logs[0]?.login_time,
      }
    }
    if (url.endsWith('/login-logs'))
      return state.loginLogs.filter((l) => l.user_id === user.id)
    if (url.endsWith('/preferences')) {
      if (method === 'get')
        return (
          state.preferences[user.id] || {
            theme: 'light',
            language: 'zh-CN',
            email_notifications: false,
          }
        )
      return commit(() => {
        state.preferences[user.id] = { ...state.preferences[user.id], ...data }
        return ok()
      })
    }
  }
  if (url.startsWith('/v1/admin/')) {
    requireAdmin()
    const match = url.match(/^\/v1\/admin\/users\/(\d+)(\/password)?$/)
    if (url === '/v1/admin/users') {
      if (method === 'get')
        return ok({
          users: state.users
            .filter((u) => !params.role || u.role === params.role)
            .map(publicUser),
        })
      if (!['TEACHER', 'ADMIN'].includes(data.role))
        throw new Error('角色须为教师或管理员')
      if (!data.username?.trim() || data.password?.length < 6)
        throw new Error('请填写用户名和至少6位密码')
      if (state.users.some((u) => u.username === data.username.trim()))
        throw new Error('用户名已存在')
      return commit(() => {
        const now = new Date().toISOString()
        const added: DemoUser = {
          ...data,
          id: nextId(state.users),
          username: data.username.trim(),
          email: data.email || '',
          is_active: true,
          created_at: now,
          updated_at: now,
        }
        state.users.push(added)
        audit(`创建账号 ${added.username}`)
        return ok(publicUser(added))
      })
    }
    if (match) {
      const target = state.users.find((u) => u.id === Number(match[1]))
      if (!target) throw new Error('用户不存在')
      if (method === 'get') return ok(publicUser(target))
      if (
        target.id === user.id &&
        (method === 'delete' ||
          data?.is_active === false ||
          (data?.role && data.role !== 'ADMIN'))
      )
        throw new Error('不能删除、禁用当前管理员或移除自身管理员角色')
      return commit(() => {
        if (match[2]) {
          if (!data.new_password || data.new_password.length < 6)
            throw new Error('新密码至少6个字符')
          target.password = data.new_password
        } else if (method === 'delete') {
          const questionIds = state.questions
            .filter((q) => q.user_id === target.id)
            .map((q) => q.id)
          state.users = state.users.filter((u) => u.id !== target.id)
          state.questions = state.questions.filter(
            (q) => q.user_id !== target.id,
          )
          state.tasks = state.tasks.filter((t) => t.user_id !== target.id)
          state.discussions = state.discussions.filter(
            (d) =>
              d.user_id !== target.id && !questionIds.includes(d.question_id),
          )
        } else {
          if (data.role && !['TEACHER', 'ADMIN'].includes(data.role))
            throw new Error('角色不正确')
          if (
            state.users.some(
              (u) => u.id !== target.id && u.username === data.username,
            )
          )
            throw new Error('用户名已存在')
          for (const key of ['username', 'email', 'role', 'is_active'] as const)
            if (data[key] !== undefined) (target as any)[key] = data[key]
          target.updated_at = new Date().toISOString()
        }
        audit(`维护账号 ${target.username}（${method}${match[2] || ''}）`)
        return ok()
      })
    }
  }
  if (url === '/v1/excellent-questions/list') {
    let questions = state.questions.filter(
      (q) => q.teacher_status === 'confirmed' && (q.rating || 0) >= 4,
    )
    if (params.keyword)
      questions = questions.filter((q) =>
        `${q.title}${q.content}`.includes(params.keyword),
      )
    questions = [...questions].sort((a, b) =>
      params.sort_by?.includes('rating')
        ? (b.rating || 0) - (a.rating || 0)
        : b.created_at.localeCompare(a.created_at),
    )
    if (params.sort_order === 'asc') questions.reverse()
    return paginate(
      questions.map((q) => ({ ...q, max_teacher_rating: q.rating })),
      params,
    )
  }
  if (url.startsWith('/v1/discussions/')) {
    const questionId = Number(params.question_id || data?.question_id)
    if (
      !url.endsWith('/delete') &&
      !state.questions.some(
        (q) =>
          q.id === questionId &&
          q.teacher_status === 'confirmed' &&
          (q.rating || 0) >= 4,
      )
    )
      throw new Error('优秀习题不存在')
    if (url.endsWith('/list')) {
      const roots = state.discussions
        .filter((d) => d.question_id === questionId && !d.parent_id)
        .map((d) => ({
          ...d,
          replies: state.discussions.filter((r) => r.parent_id === d.id),
        }))
      return paginate(roots, params)
    }
    if (url.endsWith('/post')) {
      if (!data.content?.trim()) throw new Error('请填写讨论内容')
      const parent = data.parent_id
        ? state.discussions.find(
            (d) => d.id === data.parent_id && d.question_id === questionId,
          )
        : undefined
      if (data.parent_id && !parent) throw new Error('回复的讨论已删除')
      return commit(() => {
        const discussion = {
          id: nextId(state.discussions),
          question_id: questionId,
          user_id: user.id,
          username: user.username,
          role: user.role,
          content: data.content.trim(),
          parent_id: parent?.parent_id || parent?.id || null,
          reply_to_username: parent?.username,
          created_at: new Date().toISOString(),
        }
        state.discussions.push(discussion)
        return { ...discussion, replies: [] }
      })
    }
    if (url.endsWith('/delete'))
      return commit(() => {
        const target = state.discussions.find(
          (d) => d.id === data.discussion_id,
        )
        if (!target) throw new Error('讨论已删除')
        state.discussions = state.discussions.filter(
          (d) => d.id !== target.id && d.parent_id !== target.id,
        )
        return { success: true, message: '讨论已删除' }
      })
  }
  throw new Error(`原型未接入此接口：${method} ${url}`)
}
