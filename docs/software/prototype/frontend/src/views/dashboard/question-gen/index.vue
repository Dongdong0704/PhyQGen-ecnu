<template>
  <div class="question-gen-page">
    <div class="page-heading">
      <div>
        <div class="eyebrow">TEACHING WORKSPACE</div>
        <h2>物理习题生成</h2>
        <p>从教学目标出发，生成草稿，再由您审核与定稿。</p>
      </div>
      <el-button :icon="List" @click="router.push('/tasks')"
        >查看任务记录</el-button
      >
    </div>
    <el-alert
      class="demo-note"
      title="前端交互原型 · 使用预置物理题例演示"
      description="这里会保存您的出题要求，并以预置题例模拟生成、配图和任务进度；没有调用 AI、检索服务或数据库。可完整体验草稿审核、修改、定稿与导出。"
      type="info"
      :closable="false"
      show-icon
    />
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
          <div class="scenario-hint">
            与认知目标、目标难度分别记录，用于原型展示与题库筛选。预置题例是否体现这些思维活动，仍需教师核验。
          </div>
        </el-form-item>
        <el-form-item label="补充约束（选填）" prop="context"
          ><el-input
            v-model="form.context"
            type="textarea"
            :rows="3"
            maxlength="1000"
            show-word-limit
            placeholder="可补充教学情境、解题步骤、数据范围或希望考查的思维活动。原型会记录要求，题目内容使用预置题例。"
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
              <p>
                {{
                  kbAvailable
                    ? `预置资料索引 · ${prototypeState.settings.kb_version}`
                    : '知识库当前不可用，将按普通流程演示'
                }}
              </p>
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
        <el-collapse class="demo-controls"
          ><el-collapse-item title="流程演示选项" name="scenario"
            ><el-form-item label="选择正常流程或异常场景" prop="scenario"
              ><el-select v-model="form.scenario" aria-label="流程演示场景"
                ><el-option
                  v-for="item in scenarios"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
              /></el-select>
              <div class="scenario-hint">
                {{ scenarioDescription }}
              </div></el-form-item
            ></el-collapse-item
          ></el-collapse
        >
        <div class="form-footer">
          <el-button
            class="generate-button"
            type="primary"
            size="large"
            :icon="MagicStick"
            :loading="submitting"
            @click="handleGenerate"
            >开始生成</el-button
          ><el-button size="large" @click="handleReset">重置要求</el-button
          ><span class="footer-note">生成结束后，题目仍需您人工确认。</span>
        </div>
      </el-form>
    </el-card>
    <TaskProgress v-if="currentTask" :task="currentTask" />
    <el-card v-else class="recent-card"
      ><div class="empty-progress">
        <el-icon :size="26"><Document /></el-icon>
        <div>
          <strong>从一份出题要求开始</strong>
          <p>提交后将在此展示任务阶段、逐题进度与生成的草稿。</p>
        </div>
      </div></el-card
    >
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { MagicStick, List, Document } from '@element-plus/icons-vue'
import TaskProgress from '@/components/prototype/TaskProgress.vue'
import {
  prototypeState,
  createGenerationTask,
  getCurrentUser,
} from '@/prototype/store'
import type { GenerationParams } from '@/prototype/types'

const router = useRouter()
const route = useRoute()
const formRef = ref<FormInstance>()
const submitting = ref(false)
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
const scenarios: {
  value: GenerationParams['scenario']
  label: string
  description: string
}[] = [
  {
    value: 'normal',
    label: '正常生成',
    description: '完整演示单题或批量生成，完成后逐题进入待教师人工审核。',
  },
  {
    value: 'partial_failure',
    label: '批量部分失败',
    description: '建议生成 3～5 道，观察失败题目及其余草稿同时保留。',
  },
  {
    value: 'all_failure',
    label: '全部生成失败',
    description: '任务没有可用草稿时显示失败，不以占位题目补足数量。',
  },
  {
    value: 'image_failure',
    label: '配图生成异常',
    description: '请同时开启配图。保留文本草稿，人工补全图片后才可确认定稿。',
  },
  {
    value: 'kb_miss',
    label: '知识库未命中',
    description:
      '请开启知识库增强。演示未找到证据时按普通流程继续，且不展示虚构引用。',
  },
  {
    value: 'kb_error',
    label: '知识检索异常',
    description: '请开启知识库增强。演示检索异常后的提示和降级生成。',
  },
  {
    value: 'save_failure',
    label: '草稿保存失败',
    description: '演示草稿暂存失败，不能显示保存成功，也不进入已保存题库。',
  },
  {
    value: 'timeout',
    label: '模型调用超时',
    description: '演示调用超时后的错误提示及已有可用内容保留。',
  },
]
const defaults = (): GenerationParams => ({
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
  scenario: 'normal',
})
const form = reactive<GenerationParams>(defaults())
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
const kbAvailable = computed(
  () =>
    prototypeState.settings.kb_enabled &&
    prototypeState.settings.kb_status === '可用',
)
const scenarioDescription = computed(
  () => scenarios.find((item) => item.value === form.scenario)?.description,
)
const currentTask = computed(() => {
  const id = String(route.query.task_id || '')
  if (!id) return undefined
  return prototypeState.tasks.find(
    (task) => task.id === id && task.user_id === getCurrentUser()?.id,
  )
})

watch(
  () => currentTask.value?.id,
  () => {
    if (currentTask.value)
      Object.assign(form, currentTask.value.params, {
        thinking_tags: [...(currentTask.value.params.thinking_tags || [])],
      })
  },
  { immediate: true },
)

async function handleGenerate() {
  if (submitting.value) return
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const task = createGenerationTask({
      ...form,
      knowledge_point: form.knowledge_point.trim(),
      context: form.context?.trim(),
    })
    await router.replace({
      path: '/question-gen',
      query: { task_id: task.id },
    })
    ElMessage.success('演示任务已创建，可继续浏览其他页面')
  } catch (error) {
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
.demo-note {
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
.scenario-hint {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 9px;
  line-height: 1.7;
}
.demo-controls {
  border-top-color: #edf2fa;
  border-bottom-color: #edf2fa;
}
.demo-controls :deep(.el-collapse-item__header) {
  color: var(--color-text-secondary);
}
.demo-controls :deep(.el-collapse-item__content) {
  padding-bottom: 2px;
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
