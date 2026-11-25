export type Role = 'TEACHER' | 'ADMIN'
export interface DemoUser {
  id: number
  username: string
  email: string
  role: Role
  is_active: boolean
  password: string
  created_at: string
  updated_at: string
  avatar_url?: string
}
export interface Evidence {
  source: string
  fragment_id: string
  index_version: string
  content: string
}
export interface QuestionVersion {
  version: number
  title: string
  content: string
  options?: string
  answer: string
  explanation: string
  illustration_url?: string
  created_at: string
  source: 'system' | 'teacher'
}
export interface PrototypeQuestion {
  id: number
  user_id: number
  task_id: string
  title: string
  content: string
  question_type: string
  grade: string
  bloom_level: string
  difficulty: string
  knowledge_point: string
  options?: string
  answer: string
  explanation: string
  thinking_tags?: string[]
  illustration_url?: string
  require_illustration: boolean
  created_at: string
  updated_at: string
  rating?: number
  comment?: string
  teacher_status: 'pending' | 'confirmed'
  version: number
  versions: QuestionVersion[]
  evidence: Evidence[]
  kb_reason: string
  confirmations: {
    version: number
    teacher_id: number
    teacher_name: string
    confirmed_at: string
  }[]
}
export interface GenerationParams {
  knowledge_point: string
  grade: string
  question_type: string
  bloom_level: string
  difficulty: string
  count: number
  require_illustration: boolean
  use_kb: boolean
  context?: string
  thinking_tags?: string[]
  scenario:
    | 'normal'
    | 'partial_failure'
    | 'all_failure'
    | 'image_failure'
    | 'kb_miss'
    | 'kb_error'
    | 'save_failure'
    | 'timeout'
}
export interface TaskItem {
  index: number
  stage: string
  progress: number
  attempt: number
  status: 'pending' | 'running' | 'draft' | 'failed'
  question_id?: number
  error?: string
  retained_draft?: PrototypeQuestion
}
export interface GenerationTask {
  id: string
  user_id: number
  params: GenerationParams
  created_at: string
  stage: string
  progress: number
  completed: boolean
  error?: string
  items: TaskItem[]
}
export type Task = GenerationTask
export interface Settings {
  text_model: string
  image_model: string
  embedding_model: string
  endpoint: string
  concurrency: number
  max_rounds: number
  kb_enabled: boolean
  kb_version: string
  kb_status: string
  kb_fragments: number
  registration_key: string
}
export interface Discussion {
  id: number
  question_id: number
  user_id: number
  username: string
  role: string
  content: string
  parent_id: number | null
  reply_to_username?: string
  created_at: string
}
