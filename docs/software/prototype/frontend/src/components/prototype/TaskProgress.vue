<template>
  <el-card class="task-progress">
    <template #header
      ><div class="progress-heading">
        <div>
          <h3>
            {{ task.completed ? '任务结果' : '正在生成草稿' }}
            <el-tag size="small" :type="taskType">{{ task.stage }}</el-tag>
          </h3>
          <p class="task-id">
            {{ task.id }} · {{ formatTime(task.created_at) }}
          </p>
        </div>
        <el-button
          text
          type="primary"
          @click="router.push({ path: '/tasks', query: { task_id: task.id } })"
          >任务详情 <el-icon><ArrowRight /></el-icon
        ></el-button></div
    ></template>
    <div class="task-parameters">
      <span>{{ task.params.knowledge_point }}</span
      ><el-tag size="small" effect="plain">{{ task.params.grade }}</el-tag
      ><el-tag size="small" effect="plain" type="info">{{
        questionType(task.params.question_type)
      }}</el-tag
      ><span
        >{{ bloomLabel(task.params.bloom_level) }} /
        {{ task.params.difficulty }}</span
      ><span
        >配图：{{ task.params.require_illustration ? '需要' : '无需' }}</span
      ><span>知识库：{{ task.params.use_kb ? '开启' : '关闭' }}</span>
    </div>
    <div v-if="task.params.context" class="task-context">
      补充约束：{{ task.params.context }}
    </div>
    <el-progress
      :percentage="Math.round(task.progress)"
      :status="
        task.completed ? (draftCount ? 'success' : 'exception') : undefined
      "
      :stroke-width="12"
    />
    <div class="summary-grid">
      <div>
        <strong>{{ task.params.count }}</strong
        ><span>请求题目</span>
      </div>
      <div>
        <strong class="success-number">{{ draftCount }}</strong
        ><span>已暂存草稿</span>
      </div>
      <div>
        <strong :class="{ 'error-number': failedCount }">{{
          failedCount
        }}</strong
        ><span>逐题失败</span>
      </div>
      <div>
        <strong>{{ confirmedCount }}</strong
        ><span>教师已确认</span>
      </div>
    </div>
    <el-alert
      v-if="task.error"
      :title="task.error"
      :type="draftCount ? 'warning' : 'error'"
      :closable="false"
      show-icon
      class="result-note"
    />
    <el-alert
      v-if="task.completed && draftCount"
      :title="
        confirmedCount === draftCount
          ? '本任务草稿均已由教师确认'
          : '草稿已暂存，等待教师人工审核'
      "
      :description="
        confirmedCount === draftCount
          ? '可进入题库查看确认记录，并导出已确认的题目版本。'
          : '任务完成不代表教师已确认。请打开草稿核验题目内容，直接修改并确认定稿后再导出。'
      "
      type="info"
      :closable="false"
      show-icon
      class="result-note"
    />
    <div class="item-list">
      <div
        v-for="item in task.items"
        :key="item.index"
        class="item-card"
        :class="{ 'item-failed': item.status === 'failed' }"
      >
        <div class="item-heading">
          <div class="item-title">
            <span class="item-number">{{ item.index }}</span
            ><strong>{{
              question(item.question_id)?.title ||
              item.retained_draft?.title ||
              `第 ${item.index} 道习题`
            }}</strong>
          </div>
          <el-tag
            size="small"
            :type="
              item.status === 'failed'
                ? 'danger'
                : item.status === 'draft'
                  ? 'success'
                  : 'info'
            "
            >{{ item.stage }}</el-tag
          >
        </div>
        <div class="item-meta">
          <span
            >尝试 {{ item.attempt }} /
            {{ prototypeState.settings.max_rounds }} 轮</span
          ><span>进度 {{ Math.round(item.progress) }}%</span
          ><el-tag
            v-if="question(item.question_id)"
            size="small"
            :type="
              question(item.question_id)?.teacher_status === 'confirmed'
                ? 'success'
                : 'warning'
            "
            >{{
              question(item.question_id)?.teacher_status === 'confirmed'
                ? '教师已确认'
                : '待教师人工审核'
            }}</el-tag
          >
        </div>
        <el-progress
          v-if="item.status === 'pending' || item.status === 'running'"
          :percentage="Math.round(item.progress)"
          :show-text="false"
          :stroke-width="5"
        />
        <p v-if="item.error" class="item-error">
          <el-icon><Warning /></el-icon>{{ item.error }}
        </p>
        <div v-if="item.retained_draft" class="recovery-panel">
          <div class="recovery-heading">
            <strong>未入库内容已保留</strong
            ><el-button
              size="small"
              plain
              @click="copyRetained(item.retained_draft)"
              >复制当前内容</el-button
            >
          </div>
          <p class="recovery-note">
            以下内容保留在任务记录中，尚未作为题库草稿保存，不能确认定稿或导出。
          </p>
          <div class="recovery-content">{{ item.retained_draft.content }}</div>
          <div v-if="item.retained_draft.options" class="recovery-content">
            选项：{{ item.retained_draft.options }}
          </div>
          <el-collapse
            ><el-collapse-item
              title="查看保留的答案与解析"
              :name="`retained-${item.index}`"
              ><div class="recovery-content">
                答案：{{ item.retained_draft.answer }}
              </div>
              <div class="recovery-content">
                解析：{{ item.retained_draft.explanation }}
              </div></el-collapse-item
            ></el-collapse
          >
        </div>
        <p
          v-if="item.status === 'draft' && !question(item.question_id)"
          class="kb-note"
        >
          对应题目已从题库删除，任务保留原始生成记录。
        </p>
        <template v-if="question(item.question_id)">
          <div
            class="draft-preview"
            v-html="parseMarkdown(question(item.question_id)?.content || '')"
          />
          <div class="item-bottom">
            <p class="kb-note">{{ question(item.question_id)?.kb_reason }}</p>
            <el-button
              type="primary"
              plain
              size="small"
              @click="openQuestion(item.question_id)"
              >{{
                question(item.question_id)?.teacher_status === 'confirmed'
                  ? '查看定稿'
                  : '打开草稿，人工审核'
              }}<el-icon class="button-arrow"><ArrowRight /></el-icon
            ></el-button>
          </div>
        </template>
      </div>
    </div>
    <p class="prototype-caption">
      预置题例与阶段进度仅用于原型演示；题目详情中可查看示例资料来源。
    </p>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight, Warning } from '@element-plus/icons-vue'
import { prototypeState } from '@/prototype/store'
import { parseMarkdown } from '@/utils/markdown'
import type { GenerationTask, PrototypeQuestion } from '@/prototype/types'
const props = defineProps<{ task: GenerationTask }>()
const router = useRouter()
const draftCount = computed(
  () => props.task.items.filter((item) => item.status === 'draft').length,
)
const failedCount = computed(
  () => props.task.items.filter((item) => item.status === 'failed').length,
)
const confirmedCount = computed(
  () =>
    props.task.items.filter(
      (item) => question(item.question_id)?.teacher_status === 'confirmed',
    ).length,
)
const taskType = computed(() =>
  !props.task.completed ? 'primary' : draftCount.value ? 'success' : 'danger',
)
function question(id?: number) {
  return prototypeState.questions.find(
    (question) => question.id === id && question.user_id === props.task.user_id,
  )
}
function openQuestion(id?: number) {
  if (id !== undefined)
    router.push({ path: '/question-bank', query: { question_id: id } })
}
function questionType(value: string) {
  return (
    (
      {
        single_choice: '单选题',
        multiple_choice: '多选题',
        fill_blank: '填空题',
        short_answer: '简答题',
      } as Record<string, string>
    )[value] || value
  )
}
function bloomLabel(value: string) {
  return (
    (
      {
        remember: '记忆',
        understand: '理解',
        apply: '应用',
        analyze: '分析',
      } as Record<string, string>
    )[value] || value
  )
}
function formatTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}
async function copyRetained(draft: PrototypeQuestion) {
  const text = [
    draft.title,
    `年级：${draft.grade}；题型：${questionType(draft.question_type)}；认知目标：${bloomLabel(draft.bloom_level)}；目标难度：${draft.difficulty}`,
    draft.content,
    draft.options ? `选项：${draft.options}` : '',
    `答案：${draft.answer}`,
    `解析：${draft.explanation}`,
    draft.illustration_url ? `配图引用：${draft.illustration_url}` : '',
  ]
    .filter(Boolean)
    .join('\n\n')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('当前保留内容已复制')
  } catch {
    ElMessage.warning('浏览器未允许复制，请在保留内容中选择文本手动复制')
  }
}
</script>

<style scoped>
.task-progress {
  width: 100%;
}
.progress-heading,
.item-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 15px;
}
.progress-heading h3 {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 17px;
}
.task-id {
  color: var(--color-text-secondary);
  font-size: 12px;
  margin-top: 9px;
  overflow-wrap: anywhere;
}
.task-parameters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
  font-size: 13px;
  color: var(--color-text-regular);
}
.task-parameters > span:first-child {
  font-weight: 600;
}
.task-context {
  padding: 10px 13px;
  border-radius: 7px;
  background: #f6f9ff;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.7;
  margin-bottom: 19px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  margin: 23px 0;
  padding: 18px 8px;
  background: #f6f9ff;
  border-radius: 10px;
}
.summary-grid > div {
  display: flex;
  flex-direction: column;
  gap: 7px;
  align-items: center;
  border-right: 1px solid #e4ecfa;
}
.summary-grid > div:last-child {
  border: 0;
}
.summary-grid strong {
  font-size: 24px;
  font-weight: 650;
}
.summary-grid span {
  color: var(--color-text-secondary);
  font-size: 12px;
}
.success-number {
  color: #4ca47b;
}
.error-number {
  color: #e46868;
}
.result-note {
  margin-bottom: 18px;
}
.item-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.item-card {
  border: 1px solid #e5edfa;
  padding: 18px;
  border-radius: 11px;
}
.item-failed {
  background: #fffbfb;
  border-color: #f4dcdc;
}
.item-title {
  display: flex;
  gap: 11px;
  align-items: center;
  min-width: 0;
}
.item-title strong {
  font-size: 14px;
  overflow-wrap: anywhere;
  font-weight: 550;
}
.item-number {
  display: inline-flex;
  width: 27px;
  height: 27px;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 12px;
  background: #edf4ff;
  border-radius: 8px;
  color: var(--color-primary);
}
.item-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 15px;
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 12px 0;
}
.item-error {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  color: #c65b5b;
  font-size: 13px;
  line-height: 1.8;
  margin-top: 9px;
}
.item-error .el-icon {
  margin-top: 5px;
  flex-shrink: 0;
}
.draft-preview {
  max-height: 83px;
  overflow: hidden;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-size: 13px;
  line-height: 1.8;
  color: var(--color-text-regular);
  padding: 11px 13px;
  background: #f8faff;
  border-radius: 8px;
}
.item-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  margin-top: 15px;
}
.kb-note {
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.7;
  flex: 1;
}
.button-arrow {
  margin-left: 5px;
}
.prototype-caption {
  margin-top: 19px;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.7;
}
.recovery-panel {
  margin-top: 14px;
  padding: 15px;
  border: 1px dashed #e6bf86;
  border-radius: 9px;
  background: #fffdf8;
}
.recovery-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.recovery-heading strong {
  font-size: 13px;
  color: #9c712f;
}
.recovery-note {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.7;
  margin: 8px 0 12px;
}
.recovery-content {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-size: 13px;
  color: var(--color-text-regular);
  line-height: 1.8;
  user-select: text;
}
.recovery-panel :deep(.el-collapse) {
  margin-top: 10px;
}
.recovery-panel :deep(.el-collapse-item__header),
.recovery-panel :deep(.el-collapse-item__wrap) {
  background: transparent;
}
@media (max-width: 680px) {
  .progress-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 8px;
  }
  .item-heading {
    align-items: flex-start;
  }
  .item-bottom {
    align-items: flex-start;
    flex-direction: column;
  }
  .summary-grid {
    gap: 8px;
  }
  .summary-grid strong {
    font-size: 21px;
  }
  .item-card {
    padding: 14px;
  }
}
</style>
