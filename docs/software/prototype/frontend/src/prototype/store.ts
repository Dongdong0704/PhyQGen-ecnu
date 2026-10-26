import { reactive } from 'vue'
import { demoUsers, makeExample, seedQuestions, snapshot } from './seeds'
import type {
  DemoUser,
  Discussion,
  GenerationParams,
  GenerationTask,
  PrototypeQuestion,
  Settings,
} from './types'

const STORAGE_KEY = 'phyqgen.prototype.v1'
interface State {
  users: DemoUser[]
  questions: PrototypeQuestion[]
  tasks: GenerationTask[]
  discussions: Discussion[]
  settings: Settings
  audits: { action: string; actor: string; time: string }[]
  preferences: Record<number, Record<string, unknown>>
  loginLogs: {
    id: number
    user_id: number
    ip_address: string
    user_agent: string
    login_status: string
    login_time: string
  }[]
}
const defaults = (): State => ({
  users: structuredClone(demoUsers),
  questions: seedQuestions(),
  tasks: [],
  discussions: [],
  audits: [],
  loginLogs: [],
  preferences: {},
  settings: {
    text_model: '演示文本模型',
    image_model: '演示配图模型',
    embedding_model: '演示嵌入模型',
    endpoint: 'http://localhost:8000',
    concurrency: 2,
    max_rounds: 3,
    kb_enabled: true,
    kb_version: 'demo-index-v1',
    kb_status: '可用',
    kb_fragments: 3,
    registration_key: '演示环境不开放管理员注册',
  },
})
function readState(): State {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaults()
    const parsed = JSON.parse(raw)
    if (
      !Array.isArray(parsed.users) ||
      !Array.isArray(parsed.questions) ||
      !Array.isArray(parsed.tasks) ||
      !parsed.settings
    )
      throw new Error('invalid state')
    return { ...defaults(), ...parsed }
  } catch {
    return defaults()
  }
}
export const prototypeState = reactive<State>(readState())
export const storageError = reactive({ message: '' })
function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

/** Commit before reporting success; restore the previous in-memory state if browser storage fails. */
export function commit<T>(mutate: () => T): T {
  const previous = clone(prototypeState)
  try {
    const result = mutate()
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prototypeState))
    storageError.message = ''
    return result
  } catch (error) {
    Object.assign(prototypeState, previous)
    storageError.message =
      '本地保存失败，请检查浏览器存储空间；当前操作未保存。'
    throw new Error(
      error instanceof Error && !/quota|storage/i.test(error.message)
        ? error.message
        : storageError.message,
    )
  }
}

export function getCurrentUser(): DemoUser {
  const token = localStorage.getItem('phyqgen.token') || ''
  const id = Number(token.replace('demo-session-', ''))
  const user = prototypeState.users.find((u) => u.id === id && u.is_active)
  if (!token.startsWith('demo-session-') || !user)
    throw new Error('登录已失效，请重新登录')
  return user
}
export function requireAdmin(): DemoUser {
  const user = getCurrentUser()
  if (user.role !== 'ADMIN') throw new Error('此操作需要管理员身份')
  return user
}
function ownQuestion(id: number): PrototypeQuestion {
  const q = prototypeState.questions.find(
    (q) => q.id === id && q.user_id === getCurrentUser().id,
  )
  if (!q) throw new Error('题目不存在，或不属于当前教师')
  return q
}
const nextId = (items: { id: number }[]) =>
  Math.max(0, ...items.map((i) => i.id)) + 1
export function audit(action: string) {
  prototypeState.audits.unshift({
    action,
    actor: getCurrentUser().username,
    time: new Date().toISOString(),
  })
}
export function loginLocal(username: string, password: string): DemoUser {
  const user = prototypeState.users.find((u) => u.username === username.trim())
  if (!user || user.password !== password) throw new Error('用户名或密码错误')
  if (!user.is_active) throw new Error('账号已禁用，请联系管理员')
  commit(() =>
    prototypeState.loginLogs.unshift({
      id: nextId(prototypeState.loginLogs),
      user_id: user.id,
      ip_address: '本地演示',
      user_agent: navigator.userAgent,
      login_status: 'success',
      login_time: new Date().toISOString(),
    }),
  )
  return clone(user)
}
export function registerLocal(data: {
  username: string
  password: string
  email?: string
  role?: string
}): DemoUser {
  if (data.role && data.role !== 'TEACHER')
    throw new Error('普通注册仅支持教师账号')
  if (data.username.trim().length < 3 || data.username.trim().length > 50)
    throw new Error('用户名须为3～50个字符')
  if (data.password.length < 6) throw new Error('密码至少6个字符')
  if (prototypeState.users.some((u) => u.username === data.username.trim()))
    throw new Error('用户名已存在')
  return commit(() => {
    const user: DemoUser = {
      id: nextId(prototypeState.users),
      username: data.username.trim(),
      email: data.email || '',
      password: data.password,
      role: 'TEACHER',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    prototypeState.users.push(user)
    return clone(user)
  })
}
export function updateDraft(
  id: number,
  patch: Partial<PrototypeQuestion>,
): PrototypeQuestion {
  ownQuestion(id)
  return commit(() => {
    const q = ownQuestion(id)
    for (const key of [
      'title',
      'content',
      'answer',
      'explanation',
      'options',
      'illustration_url',
    ] as const) {
      if (Object.prototype.hasOwnProperty.call(patch, key))
        (q as unknown as Record<string, unknown>)[key] = patch[key]
    }
    q.version += 1
    q.teacher_status = 'pending'
    q.updated_at = new Date().toISOString()
    q.versions.push(snapshot(q, 'teacher'))
    return q
  })
}
export function confirmQuestion(id: number): PrototypeQuestion {
  const q = ownQuestion(id)
  for (const [label, value] of [
    ['标题', q.title],
    ['题干', q.content],
    ['答案', q.answer],
    ['解析', q.explanation],
  ])
    if (!value?.trim()) throw new Error(`请先补全${label}`)
  if (q.require_illustration && !q.illustration_url)
    throw new Error('此题要求配图，请先补充可预览的图片')
  if (q.question_type.includes('choice')) {
    let options: Record<string, string>
    try {
      options = JSON.parse(q.options || '{}')
    } catch {
      throw new Error('选项格式不正确')
    }
    if (
      Object.keys(options).length < 2 ||
      Object.values(options).some((v) => !v?.trim())
    )
      throw new Error('请补全选择题选项')
  }
  if (q.teacher_status === 'confirmed') return q
  return commit(() => {
    const current = ownQuestion(id)
    const user = getCurrentUser()
    current.confirmations.push({
      version: current.version,
      teacher_id: user.id,
      teacher_name: user.username,
      confirmed_at: new Date().toISOString(),
    })
    current.teacher_status = 'confirmed'
    current.updated_at = new Date().toISOString()
    return current
  })
}
export function removeQuestion(id: number) {
  ownQuestion(id)
  commit(() => {
    prototypeState.questions = prototypeState.questions.filter(
      (q) => q.id !== id,
    )
    prototypeState.discussions = prototypeState.discussions.filter(
      (d) => d.question_id !== id,
    )
  })
}
export function rateQuestionLocal(id: number, rating: number, comment: string) {
  if (rating < 0 || rating > 5) throw new Error('评分须为0～5星')
  ownQuestion(id)
  commit(() => {
    const q = ownQuestion(id)
    q.rating = rating
    q.comment = comment
  })
}
const labels: Record<string, string> = {
  single_choice: '单选题',
  multiple_choice: '多选题',
  fill_blank: '填空题',
  short_answer: '简答题',
  remember: '记忆',
  understand: '理解',
  apply: '应用',
  analyze: '分析',
}
export function exportQuestions(ids: number[]) {
  if (!ids.length) throw new Error('请先选择题目')
  const questions = [...new Set(ids)].map(ownQuestion)
  if (
    questions.some(
      (q) =>
        q.teacher_status !== 'confirmed' ||
        !q.confirmations.some((c) => c.version === q.version),
    )
  )
    throw new Error('只能导出当前版本已由教师确认的题目')
  downloadText(
    questions
      .map((q, i) => {
        const confirmation = q.confirmations.find(
          (c) => c.version === q.version,
        )!
        const optionText = q.options
          ? Object.entries(JSON.parse(q.options))
              .map(([k, v]) => `${k}. ${v}`)
              .join('\n')
          : ''
        return `${i + 1}. ${q.title}\n知识点：${q.knowledge_point}\n年级：${q.grade} | 题型：${labels[q.question_type] || q.question_type} | 认知目标：${labels[q.bloom_level] || q.bloom_level} | 目标难度：${q.difficulty}\n高阶思维标签：${q.thinking_tags?.join('、') || '未设置'}\n确认版本：v${q.version} | 确认人：${confirmation.teacher_name} | 确认时间：${confirmation.confirmed_at}\n\n${q.content}\n${optionText}\n\n答案：${q.answer}\n解析：${q.explanation}\n配图引用：${q.illustration_url ? new URL(q.illustration_url, location.origin).href : '无'}\n引用来源：${q.evidence.map((e) => `${e.source}（${e.fragment_id} / ${e.index_version}）`).join('；') || q.kb_reason}`
      })
      .join('\n\n========================================\n\n'),
    `PhyQGen-已确认习题-${new Date().toISOString().slice(0, 10)}.txt`,
  )
}
export function downloadText(text: string, filename: string) {
  const url = URL.createObjectURL(
    new Blob(['\uFEFF', text], { type: 'text/plain;charset=utf-8' }),
  )
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1500)
}

export function createGenerationTask(params: GenerationParams): GenerationTask {
  const user = getCurrentUser()
  if (user.role !== 'TEACHER') throw new Error('请使用教师身份创建任务')
  if (!params.knowledge_point.trim()) throw new Error('请输入知识点或命题要求')
  if (!Number.isInteger(params.count) || params.count < 1 || params.count > 5)
    throw new Error('生成数量须为1～5的整数')
  for (const [valid, value, label] of [
    [['高一', '高二', '高三'], params.grade, '年级'],
    [
      ['single_choice', 'multiple_choice', 'fill_blank', 'short_answer'],
      params.question_type,
      '题型',
    ],
    [
      ['remember', 'understand', 'apply', 'analyze'],
      params.bloom_level,
      '认知目标',
    ],
    [['基础', '中等', '困难'], params.difficulty, '目标难度'],
  ] as const)
    if (!(valid as readonly string[]).includes(value))
      throw new Error(`${label}选项不正确`)
  return commit(() => {
    const task: GenerationTask = {
      id: `TASK-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      user_id: user.id,
      params: clone(params),
      created_at: new Date().toISOString(),
      stage: '待处理',
      progress: 0,
      completed: false,
      items: Array.from({ length: params.count }, (_, i) => ({
        index: i + 1,
        stage: '待处理',
        progress: 0,
        attempt: 1,
        status: 'pending',
      })),
    }
    prototypeState.tasks.unshift(task)
    return task
  })
}

/** Clock-derived progress survives navigation and refresh; no external model or server calls. */
export function advanceTasks() {
  if (!prototypeState.tasks.some((t) => !t.completed)) return
  try {
    commit(() => {
      for (const task of prototypeState.tasks.filter((t) => !t.completed)) {
        const elapsed = Date.now() - new Date(task.created_at).getTime()
        task.items.forEach((item, i) => {
          if (item.status === 'draft' || item.status === 'failed') return
          const slot = Math.floor(
            i / Math.max(1, prototypeState.settings.concurrency),
          )
          const local = elapsed - slot * 6000
          const progress = Math.max(0, Math.min(100, Math.floor(local / 60)))
          item.progress = progress
          item.status = progress > 0 ? 'running' : 'pending'
          item.stage =
            progress === 0
              ? '待处理'
              : progress < 20 && task.params.use_kb
                ? '知识检索'
                : progress < 55
                  ? '文本生成'
                  : progress < 75 && task.params.require_illustration
                    ? '配图生成'
                    : '自动校验'
          if (progress < 100) return
          const fail =
            task.params.scenario === 'all_failure' ||
            task.params.scenario === 'timeout' ||
            (task.params.scenario === 'partial_failure' &&
              i === task.items.length - 1) ||
            task.params.scenario === 'save_failure'
          if (fail) {
            item.status = 'failed'
            item.stage = '生成失败'
            if (task.params.scenario === 'save_failure') {
              const retained: PrototypeQuestion = {
                ...makeExample(
                  task.params.knowledge_point,
                  i,
                  task.params.question_type,
                ),
                id: -(i + 1),
                user_id: task.user_id,
                task_id: task.id,
                grade: task.params.grade,
                bloom_level: task.params.bloom_level,
                difficulty: task.params.difficulty,
                require_illustration: task.params.require_illustration,
              }
              if (!task.params.require_illustration)
                retained.illustration_url = undefined
              if (!task.params.use_kb) {
                retained.evidence = []
                retained.kb_reason = '本次已关闭知识库增强。'
              }
              retained.versions = [snapshot(retained, 'system')]
              item.retained_draft = retained
              item.stage = '暂存失败'
            }
            item.error =
              task.params.scenario === 'save_failure'
                ? '演示：草稿暂存失败，本题未保存。其余已保存内容保留。'
                : task.params.scenario === 'timeout'
                  ? '演示：模型调用超时，达到重试上限，未形成可用草稿。'
                  : '演示：本题生成失败，未形成可用草稿。'
            item.attempt = prototypeState.settings.max_rounds
            return
          }
          const q: PrototypeQuestion = {
            ...makeExample(
              task.params.knowledge_point,
              i,
              task.params.question_type,
            ),
            id: nextId(prototypeState.questions),
            user_id: task.user_id,
            task_id: task.id,
            grade: task.params.grade,
            bloom_level: task.params.bloom_level,
            difficulty: task.params.difficulty,
            require_illustration: task.params.require_illustration,
          }
          q.thinking_tags = task.params.thinking_tags || []
          q.evidence = q.evidence.map((e) => ({
            ...e,
            index_version: prototypeState.settings.kb_version,
          }))
          if (
            !task.params.require_illustration ||
            task.params.scenario === 'image_failure'
          )
            q.illustration_url = undefined
          if (
            task.params.scenario === 'image_failure' &&
            task.params.require_illustration
          )
            item.error =
              '演示：配图生成失败，文本已暂存；请补充图片后确认定稿。'
          if (
            !task.params.use_kb ||
            !prototypeState.settings.kb_enabled ||
            prototypeState.settings.kb_status !== '可用' ||
            ['kb_miss', 'kb_error'].includes(task.params.scenario)
          ) {
            q.evidence = []
            q.kb_reason = !task.params.use_kb
              ? '本次已关闭知识库增强。'
              : !prototypeState.settings.kb_enabled ||
                  prototypeState.settings.kb_status !== '可用'
                ? '演示知识库不可用，按普通流程生成。'
                : task.params.scenario === 'kb_miss'
                  ? '演示：未命中匹配资料，按普通流程生成。'
                  : '演示：检索服务异常，按普通流程生成。'
          }
          q.versions = [snapshot(q, 'system')]
          prototypeState.questions.unshift(q)
          item.question_id = q.id
          item.status = 'draft'
          item.stage = '草稿已暂存'
        })
        task.progress = Math.round(
          task.items.reduce((s, i) => s + i.progress, 0) / task.items.length,
        )
        task.completed = task.items.every(
          (i) => i.status === 'draft' || i.status === 'failed',
        )
        task.stage = task.completed
          ? task.items.some((i) => i.status === 'draft')
            ? '任务完成'
            : '任务失败'
          : task.items.find((i) => i.status === 'running')?.stage || '待处理'
        task.error =
          task.completed && task.items.some((i) => i.error)
            ? task.items
                .filter((i) => i.error)
                .map((i) => `第${i.index}题：${i.error}`)
                .join('\n')
            : undefined
      }
    })
  } catch {
    /* storageError is rendered globally; the failed transition is retried without showing false success. */
  }
}
export function saveSettings(settings: Settings) {
  requireAdmin()
  if (
    !Number.isInteger(settings.concurrency) ||
    settings.concurrency < 1 ||
    settings.concurrency > 5 ||
    !Number.isInteger(settings.max_rounds) ||
    settings.max_rounds < 1 ||
    settings.max_rounds > 3
  )
    throw new Error('并发数须为1～5，最大轮次须为1～3')
  commit(() => {
    prototypeState.settings = clone(settings)
    audit('更新演示模型、知识库与任务配置')
  })
}
