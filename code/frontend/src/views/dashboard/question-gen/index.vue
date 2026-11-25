<template>
  <div class="question-gen-page">
    <div class="page-heading">
      <div>
        <div class="eyebrow">TEACHING WORKSPACE</div>
        <h2>物理习题生成</h2>
        <p>从教学目标出发，生成草稿，再由您审核与定稿。</p>
      </div>
      <el-button :icon="List" @click="showTaskRecords">查看任务记录</el-button>
    </div>
    <el-alert
      v-if="missingModelRoles.length"
      class="configuration-note"
      :title="`开始生成前，请配置${missingModelRoles.map((role) => role.label).join('、')}`"
      type="warning"
      :closable="false"
      show-icon
    >
      <el-button
        link
        type="primary"
        @click="router.push({
          path: '/settings',
          query: { tab: 'model', agent: missingModelRoles[0]?.id },
        })"
        >前往个人中心配置模型</el-button
      >
    </el-alert>
    <div class="workflow">
      <span class="active">01 设置要求</span><i>→</i><span>02 生成草稿</span
      ><i>→</i><span>03 人工审核</span><i>→</i><span>04 确认与导出</span>
    </div>
    <el-card class="form-card">
      <template #header
        ><div class="card-heading">
          <div>
            <h3>设置出题要求</h3>
            <p>认知目标描述思维活动，目标难度单独设置。</p>
          </div>
          <el-tag effect="plain">高中物理</el-tag>
        </div></template
      >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleGenerate"
      >
        <el-form-item label="知识点 / 命题要求" prop="knowledge_point">
          <el-input
            v-model="form.knowledge_point"
            maxlength="300"
            show-word-limit
            placeholder="例如：牛顿第二定律，结合水平面上物体的运动分析"
            clearable
          />
          <div class="topic-list">
            <span>试试这些：</span
            ><el-button
              v-for="topic in topics"
              :key="topic"
              text
              size="small"
              @click="form.knowledge_point = topic"
              >{{ topic }}</el-button
            >
          </div>
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="年级" prop="grade"
            ><el-select v-model="form.grade" aria-label="年级"
              ><el-option
                v-for="grade in grades"
                :key="grade"
                :label="grade"
                :value="grade" /></el-select
          ></el-form-item>
          <el-form-item label="题型" prop="question_type"
            ><el-select v-model="form.question_type" aria-label="题型"
              ><el-option
                v-for="item in questionTypes"
                :key="item.value"
                :label="item.label"
                :value="item.value" /></el-select
          ></el-form-item>
          <el-form-item label="认知目标" prop="bloom_level"
            ><el-select v-model="form.bloom_level" aria-label="认知目标"
              ><el-option
                v-for="item in bloomLevels"
                :key="item.value"
                :label="item.label"
                :value="item.value" /></el-select
          ></el-form-item>
          <el-form-item label="目标难度" prop="difficulty"
            ><el-select v-model="form.difficulty" aria-label="目标难度"
              ><el-option
                v-for="difficulty in difficulties"
                :key="difficulty"
                :label="difficulty"
                :value="difficulty" /></el-select
          ></el-form-item>
        </div>
        <el-form-item label="高阶思维标签（选填）" prop="thinking_tags">
          <el-select
            v-model="form.thinking_tags"
            multiple
            collapse-tags
            collapse-tags-tooltip
            placeholder="按教学目标选择，可多选"
            aria-label="高阶思维标签"
          >
            <el-option
              v-for="tag in thinkingTags"
              :key="tag.value"
              :label="tag.label"
              :value="tag.value"
            />
          </el-select>
          <div class="field-description">
            所选标签作为命题要求，并可在题库中用于筛选。
          </div>
        </el-form-item>
        <el-form-item label="补充约束（选填）" prop="context"
          ><el-input
            v-model="form.context"
            type="textarea"
            :rows="3"
            maxlength="1000"
            show-word-limit
            placeholder="可补充教学情境、解题步骤、数据范围或希望考查的思维活动"
        /></el-form-item>
        <div class="options-grid">
          <div class="option-card">
            <div>
              <strong>物理配图</strong>
              <p>预览与题干对应的物理示意图</p>
            </div>
            <el-switch
              v-model="form.require_illustration"
              aria-label="需要配图"
            />
          </div>
          <div class="option-card">
            <div>
              <strong>知识库增强</strong>
              <p>{{ knowledgeHint }}</p>
            </div>
            <el-switch v-model="form.use_kb" aria-label="启用知识库增强" />
          </div>
        </div>
        <div class="count-line">
          <el-form-item label="生成数量" prop="count"
            ><el-input-number
              v-model="form.count"
              :min="1"
              :max="5"
              :step="1"
              step-strictly
              controls-position="right"
              aria-label="生成数量"
            /><span class="field-hint"
              >每个任务 1～5 道；逐题保存草稿与进度。</span
            ></el-form-item
          >
        </div>
        <div class="form-footer">
          <el-button
            class="generate-button"
            type="primary"
            size="large"
            :icon="MagicStick"
            :loading="submitting"
            native-type="submit"
            >开始生成</el-button
          ><el-button size="large" @click="handleReset">重置要求</el-button
          ><span class="footer-note">生成结束后，题目仍需您人工确认。</span>
        </div>
      </el-form>
    </el-card>
    <section ref="progressSection" aria-label="生成进度与任务记录">
      <el-card class="recent-card">
        <div v-if="tasks.length" class="task-history">
          <label for="generation-history">任务记录</label>
          <el-select
            id="generation-history"
            :model-value="selectedTaskId"
            aria-label="任务记录"
            filterable
            placeholder="选择要查看的任务"
            @change="selectTask"
          >
            <el-option
              v-for="task in tasks"
              :key="task.id"
              :label="`${task.params.knowledge_point} · ${formatTime(task.created_at)}`"
              :value="task.id"
            />
          </el-select>
        </div>
        <el-alert
          v-if="historyError"
          :title="historyError"
          type="warning"
          :closable="false"
          show-icon
        >
          <el-button link type="primary" @click="loadHistory"
            >重新加载任务记录</el-button
          >
        </el-alert>
        <el-alert
          v-if="progressError"
          :title="progressError"
          type="warning"
          :closable="false"
          show-icon
        />
        <TaskProgress
          v-if="currentTask"
          :key="currentTask.id"
          :task="currentTask"
        />
        <el-skeleton
          v-else-if="historyLoading || taskLoading"
          :rows="2"
          animated
        />
        <div v-else-if="!historyError && !progressError" class="empty-progress">
          <el-icon :size="26"><Document /></el-icon>
          <div>
            <strong>从一份出题要求开始</strong>
            <p>提交后将在此展示任务阶段、逐题进度与生成的草稿。</p>
          </div>
        </div>
      </el-card>
    </section>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  nextTick,
  onMounted,
  onUnmounted,
  reactive,
  ref,
  watch,
} from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { MagicStick, List, Document } from '@element-plus/icons-vue'
import TaskProgress from '@/components/prototype/TaskProgress.vue'
import { HttpError } from '@/api/http'
import { getModelSettings, modelRoles, type ModelSettings } from '@/api/modules/model-settings'
import {
  getGenerationTask,
  getKnowledgeStatus,
  listGenerationTasks,
  startGeneration,
  type GenerationRequest,
  type LiveGenerationTask,
} from '@/api/modules/generation'

const router = useRouter()
const route = useRoute()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const progressSection = ref<HTMLElement>()
const tasks = ref<LiveGenerationTask[]>([])
const initialTaskId = ref<string>()
const modelSettings = ref<ModelSettings>()
const knowledgeHint = ref('检索相关资料，命中片段将随草稿保存')
const historyLoading = ref(false)
const taskLoading = ref(false)
const historyError = ref('')
const progressError = ref('')
const pageController = new AbortController()
const grades = ['高一', '高二', '高三']
const difficulties = ['基础', '中等', '困难']
const topics = ['牛顿第二定律', '动能定理', '闭合电路欧姆定律']
const questionTypes = [
  { value: 'single_choice', label: '单选题' },
  { value: 'multiple_choice', label: '多选题' },
  { value: 'fill_blank', label: '填空题' },
  { value: 'short_answer', label: '简答题' },
]
const bloomLevels = [
  { value: 'remember', label: '记忆 · 概念与规律' },
  { value: 'understand', label: '理解 · 解释物理情境' },
  { value: 'apply', label: '应用 · 解决具体问题' },
  { value: 'analyze', label: '分析 · 拆解关系与过程' },
]
const thinkingTags = [
  { value: 'C1', label: 'C1 · 建模与多重表征' },
  { value: 'C2', label: 'C2 · 科学推理与定量分析' },
  { value: 'C3', label: 'C3 · 证据论证与科学解释' },
  { value: 'C4', label: 'C4 · 实验设计与数据评价' },
  { value: 'C5', label: 'C5 · 批判质疑与方案创新' },
  { value: 'C6', label: 'C6 · 迁移整合与真实问题解决' },
]
const defaults = (): GenerationRequest => ({
  knowledge_point: '',
  grade: '高一',
  question_type: 'single_choice',
  bloom_level: 'apply',
  difficulty: '中等',
  thinking_tags: [],
  count: 1,
  require_illustration: false,
  use_kb: true,
  context: '',
})
const form = reactive<GenerationRequest>(defaults())
const missingModelRoles = computed(() => {
  const roles = modelSettings.value?.roles
  if (!roles) return []
  return modelRoles.filter((role) =>
    (!role.requiresIllustration || form.require_illustration) && !roles[role.id].configured,
  )
})
const rules: FormRules = {
  knowledge_point: [
    {
      required: true,
      whitespace: true,
      message: '请填写知识点或命题要求',
      trigger: 'blur',
    },
  ],
  grade: [{ required: true, message: '请选择年级', trigger: 'change' }],
  question_type: [{ required: true, message: '请选择题型', trigger: 'change' }],
  bloom_level: [
    { required: true, message: '请选择认知目标', trigger: 'change' },
  ],
  difficulty: [
    { required: true, message: '请选择目标难度', trigger: 'change' },
  ],
  count: [
    {
      validator: (_rule, value, callback) =>
        Number.isInteger(value) && value >= 1 && value <= 5
          ? callback()
          : callback(new Error('生成数量必须是 1～5 的整数')),
      trigger: 'change',
    },
  ],
}
const requestedTaskId = computed(() =>
  typeof route.query.task_id === 'string' ? route.query.task_id : undefined,
)
const selectedTaskId = computed(
  () => requestedTaskId.value || initialTaskId.value,
)
const currentTask = computed(() =>
  tasks.value.find((task) => task.id === selectedTaskId.value),
)

watch(
  [requestedTaskId, () => currentTask.value?.id],
  ([requestedId, taskId]) => {
    const params = currentTask.value?.params
    if (!params || !requestedId || requestedId !== taskId) return
    Object.assign(form, defaults(), params, {
      thinking_tags: [...(params.thinking_tags ?? [])],
    })
    formRef.value?.clearValidate()
  },
  { immediate: true },
)

watch(
  selectedTaskId,
  (id, _previousId, onCleanup) => {
    progressError.value = ''
    taskLoading.value = Boolean(id && !currentTask.value)
    if (!id) return
    const taskId = id
    const controller = new AbortController()
    let timer: number | undefined
    onCleanup(() => {
      controller.abort()
      window.clearTimeout(timer)
    })

    async function refreshTask() {
      let delay = 1200
      try {
        const task = await getGenerationTask(taskId, controller.signal)
        if (controller.signal.aborted) return
        upsertTask(task)
        progressError.value = ''
        if (task.completed) return
      } catch (error) {
        if (controller.signal.aborted) return
        if (error instanceof HttpError && error.status === 404) {
          progressError.value = '未找到该任务，请选择自己的任务记录。'
          return
        }
        progressError.value = '暂时无法更新任务进度，正在重新连接。'
        delay = 3500
      } finally {
        if (!controller.signal.aborted) taskLoading.value = false
      }
      timer = window.setTimeout(refreshTask, delay)
    }

    void refreshTask()
  },
  { immediate: true },
)

onMounted(() => {
  void loadHistory()
  void loadModelStatus()
  void loadKnowledgeStatus()
})
onUnmounted(() => pageController.abort())

async function loadModelStatus() {
  try {
    modelSettings.value = await getModelSettings(pageController.signal)
  } catch {
    // 提交时由后端核验配置，并返回可供用户处理的错误。
  }
}

async function loadKnowledgeStatus() {
  try {
    const knowledge = await getKnowledgeStatus(pageController.signal)
    knowledgeHint.value =
      knowledge.kb_enabled && knowledge.kb_fragments > 0
        ? `本地资料索引 · ${knowledge.kb_version}`
        : '知识库当前不可用，将按普通流程生成'
  } catch {
    // 具体检索状态将在逐题结果中显示。
  }
}

async function loadHistory() {
  if (historyLoading.value) return
  historyLoading.value = true
  historyError.value = ''
  try {
    const records = await listGenerationTasks(pageController.signal)
    const knownIds = new Set(tasks.value.map((task) => task.id))
    tasks.value.push(...records.filter((task) => !knownIds.has(task.id)))
    initialTaskId.value ??=
      tasks.value.find((task) => !task.completed)?.id ?? tasks.value[0]?.id
  } catch (error) {
    if (pageController.signal.aborted) return
    historyError.value =
      error instanceof Error ? error.message : '任务记录加载失败'
  } finally {
    historyLoading.value = false
  }
}

function upsertTask(task: LiveGenerationTask) {
  const index = tasks.value.findIndex((record) => record.id === task.id)
  if (index === -1) tasks.value.unshift(task)
  else tasks.value[index] = task
}

function formatTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

function showTaskRecords() {
  progressSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function selectTask(id: string) {
  return router.replace({ path: '/question-gen', query: { task_id: id } })
}

async function handleGenerate() {
  if (submitting.value) return
  submitting.value = true
  try {
    const valid = await formRef.value?.validate().catch(() => false)
    if (!valid) return
    const task = await startGeneration(
      {
        ...form,
        knowledge_point: form.knowledge_point.trim(),
        context: form.context?.trim(),
      },
      pageController.signal,
    )
    if (pageController.signal.aborted) return
    if (missingModelRoles.value.length) void loadModelStatus()
    upsertTask(task)
    await selectTask(task.id)
    await nextTick()
    showTaskRecords()
    ElMessage.success('任务已创建，草稿将逐题保存至我的题库')
  } catch (error) {
    if (pageController.signal.aborted) return
    if (error instanceof HttpError && error.status === 409)
      void loadModelStatus()
    ElMessage.error(
      error instanceof Error ? error.message : '任务创建失败，请重试',
    )
  } finally {
    submitting.value = false
  }
}
function handleReset() {
  Object.assign(form, defaults())
  formRef.value?.clearValidate()
}
</script>

<style scoped>
.question-gen-page {
  max-width: 1120px;
  width: 100%;
  margin: 0 auto;
  padding-bottom: 30px;
}
.page-heading,
.card-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}
.page-heading {
  margin-bottom: 24px;
}
.eyebrow {
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  margin-bottom: 9px;
}
.page-heading h2 {
  font-size: 25px;
  font-weight: 650;
  margin-bottom: 9px;
}
.page-heading p,
.card-heading p {
  color: var(--color-text-secondary);
  line-height: 1.7;
}
.configuration-note {
  margin-bottom: 20px;
}
.workflow {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 17px 24px;
  margin-bottom: 20px;
  border: 1px solid #e5edfa;
  border-radius: 12px;
  background: #ffffffa6;
  color: var(--color-text-secondary);
}
.workflow span {
  font-size: 13px;
}
.workflow .active {
  color: var(--color-primary);
  font-weight: 650;
}
.workflow i {
  color: #afbdd4;
  font-style: normal;
}
.card-heading h3 {
  font-size: 17px;
  margin-bottom: 5px;
}
.card-heading p {
  font-size: 13px;
}
.form-card {
  margin-bottom: 24px;
}
.form-card :deep(.el-card__body) {
  padding: 24px 28px;
}
.form-card :deep(.el-select) {
  width: 100%;
}
.form-card :deep(.el-form-item__label) {
  font-weight: 550;
  color: var(--color-text-regular);
}
.form-grid,
.options-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 24px;
}
.topic-list {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 5px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.topic-list :deep(.el-button + .el-button) {
  margin-left: 0;
}
.options-grid {
  gap: 16px;
  margin: 5px 0 23px;
}
.option-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 17px;
  background: #f7faff;
  border: 1px solid #e6eefb;
  border-radius: 10px;
}
.option-card strong {
  font-size: 14px;
  font-weight: 550;
}
.option-card p {
  color: var(--color-text-secondary);
  font-size: 12px;
  margin-top: 5px;
  line-height: 1.5;
}
.field-hint {
  margin-left: 14px;
  color: var(--color-text-secondary);
  font-size: 12px;
}
.field-description {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 9px;
  line-height: 1.7;
}
.form-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding-top: 24px;
}
.form-footer :deep(.el-button + .el-button) {
  margin-left: 0;
}
.generate-button {
  padding-left: 28px;
  padding-right: 28px;
}
.footer-note {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-left: auto;
}
.empty-progress {
  display: flex;
  gap: 18px;
  align-items: center;
  color: var(--color-text-secondary);
  padding: 8px;
}
.empty-progress strong {
  color: var(--color-text-regular);
  font-weight: 550;
}
.empty-progress p {
  margin-top: 7px;
  font-size: 13px;
}
.task-history {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px 14px;
  margin-bottom: 17px;
  color: var(--color-text-regular);
  font-size: 13px;
}
.task-history :deep(.el-select) {
  width: min(100%, 460px);
}
.recent-card :deep(.el-alert) + * {
  margin-top: 12px;
}
@media (max-width: 768px) {
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .form-grid,
  .options-grid {
    grid-template-columns: 1fr;
  }
  .workflow {
    padding: 14px 10px;
    flex-wrap: wrap;
    justify-content: center;
  }
  .workflow span {
    font-size: 12px;
  }
  .form-card :deep(.el-card__body) {
    padding: 18px;
  }
  .field-hint {
    width: 100%;
    margin: 9px 0 0;
  }
  .footer-note {
    width: 100%;
    margin: 0;
  }
}
</style>
