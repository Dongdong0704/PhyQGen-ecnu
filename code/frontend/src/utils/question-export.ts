import type { PrototypeQuestion } from '@/prototype/types'
import { downloadText } from './download'

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

export function downloadConfirmedQuestions(questions: PrototypeQuestion[]) {
  const text = questions.map((question, index) => {
    const confirmation = question.confirmations.find(
      (record) => record.version === question.version,
    )
    if (question.teacher_status !== 'confirmed' || !confirmation) {
      throw new Error('只能导出当前版本已由教师确认的题目')
    }
    const options = question.options
      ? Object.entries(JSON.parse(question.options)).map(
          ([key, value]) => `${key}. ${value}`,
        )
      : []
    const evidence = question.evidence.map(
      (item) => `${item.source}（${item.fragment_id} / ${item.index_version}）`,
    )
    const { grade, question_type, bloom_level, difficulty } = question
    const illustration = question.illustration_url
      ? new URL(question.illustration_url, location.origin).href
      : '无'
    return [
      `${index + 1}. ${question.title}`,
      `知识点：${question.knowledge_point}`,
      `年级：${grade} | 题型：${labels[question_type] || question_type} | 认知目标：${labels[bloom_level] || bloom_level} | 目标难度：${difficulty}`,
      `高阶思维标签：${question.thinking_tags?.join('、') || '未设置'}`,
      `确认版本：v${question.version} | 确认人：${confirmation.teacher_name} | 确认时间：${confirmation.confirmed_at}`,
      '',
      question.content,
      options.join('\n'),
      '',
      `答案：${question.answer}`,
      `解析：${question.explanation}`,
      `配图引用：${illustration}`,
      `引用来源：${evidence.join('；') || question.kb_reason}`,
    ].join('\n')
  })
  downloadText(
    text.join('\n\n========================================\n\n'),
    `PhyQGen-已确认习题-${new Date().toISOString().slice(0, 10)}.txt`,
  )
}
