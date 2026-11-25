import type { ExcellentQuestionDetail } from '@/api/modules/excellent-questions'
import { downloadText } from '@/utils/download'

const questionTypes = {
  single_choice: { label: '单选题', color: 'primary' },
  multiple_choice: { label: '多选题', color: 'success' },
  fill_blank: { label: '填空题', color: 'warning' },
  short_answer: { label: '简答题', color: 'info' },
} as const

const bloomLevels = {
  remember: { label: '记忆', color: 'info' },
  understand: { label: '理解', color: 'success' },
  apply: { label: '应用', color: 'warning' },
  analyze: { label: '分析', color: 'danger' },
} as const

const thinkingLabels: Record<string, string> = {
  C1: '建模与多重表征',
  C2: '科学推理与定量分析',
  C3: '证据论证与科学解释',
  C4: '实验设计与数据评价',
  C5: '批判质疑与方案创新',
  C6: '迁移整合与真实问题解决',
}

const questionType = (value: string) =>
  questionTypes[value.toLowerCase() as keyof typeof questionTypes]
const bloomLevel = (value: string) =>
  bloomLevels[value.toLowerCase() as keyof typeof bloomLevels]
export const getTypeLabel = (value: string) => questionType(value)?.label || value
export const getTypeColor = (value: string) => questionType(value)?.color || 'info'
export const getBloomLevelText = (value: string) => bloomLevel(value)?.label || value
export const getBloomLevelType = (value: string) => bloomLevel(value)?.color || 'info'

export const thinkingText = (tags?: string[]) =>
  tags?.length
    ? tags.map((tag) => thinkingLabels[tag] ? `${tag} ${thinkingLabels[tag]}` : tag).join('；')
    : '未设置'

export const difficultyLabel = (value?: string) =>
  value
    ? { easy: '基础', medium: '中等', hard: '困难' }[value] || value
    : '未记录'

export const formatDate = (date: string) =>
  new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

export function parseOptions(options: string | null | undefined): Record<string, string> | null {
  if (!options) return null
  try {
    const parsed: unknown = JSON.parse(options)
    if (
      parsed && typeof parsed === 'object' && !Array.isArray(parsed) &&
      Object.values(parsed).every((value) => typeof value === 'string')
    ) return parsed as Record<string, string>
  } catch {
    // Older or malformed options are still available as source text.
  }
  return null
}

export function getFullImageUrl(value: string | null | undefined) {
  if (!value) return ''
  try {
    const url = new URL(value, window.location.origin + '/')
    return ['http:', 'https:', 'blob:'].includes(url.protocol) || /^data:image\//i.test(url.href)
      ? url.href
      : ''
  } catch {
    return ''
  }
}

export const currentConfirmation = (question: ExcellentQuestionDetail) =>
  question.confirmations.find((record) => record.version === question.version)

export function downloadExcellentQuestion(question: ExcellentQuestionDetail) {
  const confirmation = currentConfirmation(question)
  if (question.teacher_status !== 'confirmed' || !confirmation) {
    throw new Error('当前题目已不属于优秀定稿，请刷新列表后重试')
  }

  const lines = [
    `习题：${question.title}`,
    '='.repeat(60),
    '',
    `【知识点】${question.knowledge_point}`,
    `【题型】${getTypeLabel(question.question_type)}`,
    `【认知目标】${getBloomLevelText(question.bloom_level)}`,
    `【目标难度】${difficultyLabel(question.difficulty)}`,
    `【高阶思维能力】${thinkingText(question.thinking_tags)}`,
    `【年级】${question.grade}`,
    `【教师评分】${question.max_teacher_rating} 分`,
    `【创建时间】${formatDate(question.created_at)}`,
    '【教师处理状态】教师已确认',
    `【确认版本】v${question.version}`,
    `【确认人】${confirmation.teacher_name}`,
    `【确认时间】${formatDate(confirmation.confirmed_at)}`,
    `【配图要求】${question.require_illustration ? '需要配图' : '无需配图'}`,
    '',
    '─'.repeat(60),
    '【习题内容】',
    question.content,
    '',
  ]
  if (question.options) {
    const options = parseOptions(question.options)
    lines.push(
      '─'.repeat(60), '【选项】',
      options ? Object.entries(options).map(([key, value]) => `${key}. ${value}`).join('\n') : question.options,
      '',
    )
  }
  const imageUrl = getFullImageUrl(question.illustration_url)
  if (imageUrl) lines.push('─'.repeat(60), '【配图引用】', imageUrl, '')
  lines.push('═'.repeat(60), '【答案】', question.answer, '')
  if (question.explanation) lines.push('═'.repeat(60), '【解析】', question.explanation, '')
  const evidence = question.evidence.map((item) =>
    `${item.source}\n片段：${item.fragment_id} | 索引版本：${item.index_version}\n${item.content}`,
  )
  lines.push(
    '─'.repeat(60), '【引用来源】',
    evidence.join('\n\n') || question.kb_reason || '未使用知识库增强',
  )
  const title = question.title.replace(/[<>:"/\\|?*\x00-\x1F]/g, '_').trim() || '优秀习题'
  downloadText(lines.join('\n'), `${title}-v${question.version}.txt`)
}
