<template>
  <div class="question-manage-page">
    <el-card class="header-card">
      <div class="page-header">
        <div class="title-section">
          <el-tag effect="dark">题库工作台</el-tag>
          <h2>我的题库</h2>
          <p class="subtitle">直接审核和修改习题，确认当前版本后即可导出。</p>
        </div>
        <el-button
          type="primary"
          :icon="Plus"
          @click="router.push('/question-gen')"
          >生成新习题</el-button
        >
      </div>
      <div class="summary-row">
        <span
          >全部习题 <strong>{{ ownQuestions.length }}</strong></span
        >
        <span
          >待教师人工审核
          <strong>{{
            ownQuestions.filter((q) => q.teacher_status === 'pending').length
          }}</strong></span
        >
        <span
          >教师已确认
          <strong>{{
            ownQuestions.filter((q) => q.teacher_status === 'confirmed').length
          }}</strong></span
        >
      </div>
    </el-card>
    <el-card class="filter-card">
      <div class="filter-bar">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索标题或题干"
          clearable
          :prefix-icon="Search"
          aria-label="搜索标题或题干"
        />
        <el-select
          v-model="filters.type"
          placeholder="全部题型"
          clearable
          aria-label="题型筛选"
          ><el-option
            v-for="(label, value) in typeLabels"
            :key="value"
            :label="label"
            :value="value"
        /></el-select>
        <el-select
          v-model="filters.knowledge"
          placeholder="全部知识点"
          clearable
          aria-label="知识点筛选"
          ><el-option
            v-for="point in knowledgePoints"
            :key="point"
            :label="point"
            :value="point"
        /></el-select>
        <el-select
          v-model="filters.bloom"
          placeholder="全部认知目标"
          clearable
          aria-label="认知目标筛选"
          ><el-option
            v-for="(label, value) in bloomLabels"
            :key="value"
            :label="label"
            :value="value"
        /></el-select>
        <el-select
          v-model="filters.status"
          placeholder="全部确认状态"
          clearable
          aria-label="确认状态筛选"
          ><el-option label="待教师人工审核" value="pending" /><el-option
            label="教师已确认"
            value="confirmed"
        /></el-select>
        <el-button @click="resetFilters">重置筛选</el-button>
      </div>
      <div class="thinking-filter-row">
        <span>高阶思维能力</span>
        <el-select
          v-model="filters.thinking"
          placeholder="全部高阶思维标签"
          clearable
          aria-label="高阶思维标签筛选"
          style="width: 300px"
        >
          <el-option
            v-for="(label, code) in thinkingLabels"
            :key="code"
            :label="code + ' ' + label"
            :value="code"
          />
        </el-select>
        <span class="export-hint">与认知目标、目标难度分别记录</span>
      </div>
      <div class="list-toolbar">
        <div class="selection-tools">
          <el-checkbox
            :model-value="allPageSelected"
            :indeterminate="somePageSelected"
            @change="togglePageSelection"
            >选择本页</el-checkbox
          ><span>已选 {{ selectedIds.length }} 题</span
          ><el-button v-if="selectedIds.length" text @click="selectedIds = []"
            >清空选择</el-button
          ><el-button
            type="success"
            plain
            :icon="Download"
            :disabled="selectedIds.length === 0"
            @click="exportSelected"
            >批量导出 TXT</el-button
          >
        </div>
        <el-select v-model="sort" style="width: 170px" aria-label="题库排序"
          ><el-option label="创建时间：由新到旧" value="newest" /><el-option
            label="创建时间：由旧到新"
            value="oldest" /><el-option label="评分：由高到低" value="rating"
        /></el-select>
      </div>
      <p class="export-hint">选中题目须全部为当前版本的定稿，才可批量导出。</p>
    </el-card>
    <el-card class="list-card">
      <el-empty
        v-if="filteredQuestions.length === 0"
        description="没有符合条件的习题"
        ><el-button @click="resetFilters">清除筛选</el-button></el-empty
      >
      <div v-else class="question-list">
        <article
          v-for="item in pageQuestions"
          :key="item.id"
          class="question-item"
          :data-question-id="item.id"
        >
          <div class="question-header">
            <el-checkbox
              :model-value="selectedIds.includes(item.id)"
              :aria-label="'选择习题：' + item.title"
              @change="toggleSelection(item.id, Boolean($event))"
            />
            <div class="question-heading">
              <div class="question-tags">
                <el-tag size="small">{{ typeLabel(item.question_type) }}</el-tag
                ><el-tag size="small" type="info">{{
                  bloomLabel(item.bloom_level)
                }}</el-tag
                ><el-tag
                  size="small"
                  :type="
                    item.teacher_status === 'confirmed' ? 'success' : 'warning'
                  "
                  >{{ statusLabel(item.teacher_status) }}</el-tag
                ><el-tag
                  v-if="item.illustration_url"
                  size="small"
                  type="success"
                  effect="plain"
                  >含配图</el-tag
                ><el-tag
                  v-else-if="item.require_illustration"
                  size="small"
                  type="danger"
                  effect="plain"
                  >配图待补全</el-tag
                >
              </div>
              <h3>{{ item.title || '未命名草稿' }}</h3>
              <p class="question-meta">
                {{ item.grade }} · {{ item.knowledge_point }} ·
                {{ difficultyLabel(item.difficulty) }} · v{{ item.version }} ·
                {{ formatDate(item.created_at) }}
              </p>
              <div v-if="item.thinking_tags?.length" class="thinking-tags">
                <span>高阶思维</span>
                <el-tag
                  v-for="tag in item.thinking_tags"
                  :key="tag"
                  size="small"
                  type="success"
                  effect="plain"
                  >{{ tag }} {{ thinkingLabels[tag] || tag }}</el-tag
                >
              </div>
            </div>
          </div>
          <div class="content-preview" v-html="parseMarkdown(item.content)" />
          <div class="question-footer">
            <div class="rating-section">
              <span>我的评分</span
              ><el-rate :model-value="item.rating || 0" disabled /><el-button
                text
                @click="openRating(item)"
                >评分 / 评价</el-button
              >
            </div>
            <div class="action-section">
              <el-button
                size="small"
                type="primary"
                plain
                :icon="View"
                @click="openDetail(item)"
                >详情与审核</el-button
              ><el-button size="small" :icon="Edit" @click="openEdit(item)"
                >修改草稿</el-button
              ><el-button
                v-if="item.teacher_status !== 'confirmed'"
                size="small"
                type="success"
                @click="confirmCurrent(item)"
                >确认定稿</el-button
              ><el-button
                size="small"
                :icon="Download"
                :disabled="item.teacher_status !== 'confirmed'"
                @click="exportOne(item.id)"
                >导出</el-button
              ><el-button
                size="small"
                type="danger"
                plain
                :icon="Delete"
                @click="deleteCurrent(item)"
                >删除</el-button
              >
            </div>
          </div>
          <p v-if="item.comment" class="comment-section">
            我的评价：{{ item.comment }}
          </p>
        </article>
      </div>
      <div v-if="filteredQuestions.length" class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="filteredQuestions.length"
          :page-sizes="[5, 10, 20]"
          layout="total, sizes, prev, pager, next"
        />
      </div>
    </el-card>
    <el-dialog
      v-model="detailVisible"
      title="习题详情与教师人工审核"
      width="min(960px, 94vw)"
      :close-on-click-modal="false"
    >
      <div v-if="currentQuestion" class="detail-content">
        <div class="detail-heading">
          <h2>{{ currentQuestion.title || '未命名草稿' }}</h2>
          <el-tag
            :type="
              currentQuestion.teacher_status === 'confirmed'
                ? 'success'
                : 'warning'
            "
            >{{ statusLabel(currentQuestion.teacher_status) }} · v{{
              currentQuestion.version
            }}</el-tag
          >
        </div>
        <p class="question-meta">
          {{ currentQuestion.grade }} · {{ currentQuestion.knowledge_point }} ·
          {{ typeLabel(currentQuestion.question_type) }} ·
          {{ bloomLabel(currentQuestion.bloom_level) }} ·
          {{ difficultyLabel(currentQuestion.difficulty) }}
        </p>
        <div class="thinking-tags">
          <span>高阶思维能力</span>
          <el-tag
            v-for="tag in currentQuestion.thinking_tags || []"
            :key="tag"
            type="success"
            effect="plain"
            >{{ tag }} {{ thinkingLabels[tag] || tag }}</el-tag
          >
          <span
            v-if="!currentQuestion.thinking_tags?.length"
            class="question-meta"
            >未设置</span
          >
        </div>
        <el-tabs v-model="detailTab">
          <el-tab-pane label="题目与人工审核" name="content">
            <el-alert
              v-if="currentQuestion.teacher_status === 'pending'"
              type="info"
              :closable="false"
              title="请核验题干、答案、解析和配图，完成教学适配性检查后明确执行「确认定稿」。"
              show-icon
            />
            <QuestionPreview
              :key="currentQuestion.id + ':' + currentQuestion.version"
              :question="currentQuestion"
            />
            <div v-if="currentConfirmation" class="confirmation-record">
              确认人：{{ currentConfirmation.teacher_name }} · 确认版本：v{{
                currentConfirmation.version
              }}
              · {{ formatDate(currentConfirmation.confirmed_at) }}
            </div>
          </el-tab-pane>
          <el-tab-pane label="引用来源" name="evidence"
            ><el-empty
              v-if="!currentQuestion.evidence.length"
              :description="currentQuestion.kb_reason || '本题未使用知识库增强'"
            />
            <div
              v-for="evidence in currentQuestion.evidence"
              :key="evidence.fragment_id"
              class="evidence-card"
            >
              <h4>{{ evidence.source }}</h4>
              <p class="question-meta">
                片段 {{ evidence.fragment_id }} · 索引
                {{ evidence.index_version }}
              </p>
              <p class="evidence-text">{{ evidence.content }}</p>
            </div></el-tab-pane
          >
          <el-tab-pane
            :label="'版本记录（' + currentQuestion.versions.length + '）'"
            name="history"
          >
            <el-collapse
              ><el-collapse-item
                v-for="version in [...currentQuestion.versions].reverse()"
                :key="version.version"
                :name="version.version"
                ><template #title
                  ><span class="version-title"
                    >v{{ version.version }} ·
                    {{ version.source === 'teacher' ? '教师修改' : '系统生成' }}
                    · {{ formatDate(version.created_at) }}</span
                  ><el-tag
                    v-if="version.version === currentQuestion.version"
                    size="small"
                    >当前版本</el-tag
                  ></template
                >
                <h3>{{ version.title }}</h3>
                <QuestionPreview :question="version" />
                <div
                  v-for="record in currentQuestion.confirmations.filter(
                    (c) => c.version === version.version,
                  )"
                  :key="record.confirmed_at"
                  class="confirmation-record"
                >
                  此版本由 {{ record.teacher_name }} 于
                  {{ formatDate(record.confirmed_at) }} 确认
                </div></el-collapse-item
              ></el-collapse
            >
          </el-tab-pane>
        </el-tabs>
      </div>
      <template #footer
        ><el-button @click="detailVisible = false">关闭</el-button
        ><template v-if="currentQuestion"
          ><el-button :icon="Edit" @click="openEdit(currentQuestion)"
            >修改草稿</el-button
          ><el-button
            v-if="currentQuestion.teacher_status === 'confirmed'"
            type="success"
            :icon="Download"
            @click="exportOne(currentQuestion.id)"
            >导出定稿 TXT</el-button
          ><el-button
            v-else
            type="success"
            :loading="confirming"
            @click="confirmCurrent(currentQuestion)"
            >确认定稿</el-button
          ></template
        ></template
      >
    </el-dialog>
    <el-dialog
      v-model="editVisible"
      title="教师修改习题"
      width="min(1240px, 96vw)"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :before-close="beforeCloseEdit"
    >
      <el-alert
        type="warning"
        :closable="false"
        title="保存后形成新版本，并回到待教师人工审核状态。请核验新版本后再次确认定稿。"
        show-icon
      />
      <div class="editor-layout">
        <el-form class="editor-form" label-position="top">
          <el-form-item label="标题"
            ><el-input v-model="editForm.title" maxlength="160" show-word-limit
          /></el-form-item>
          <el-form-item label="题干（支持 Markdown 与 LaTeX）"
            ><el-input v-model="editForm.content" type="textarea" :rows="7"
          /></el-form-item>
          <el-form-item
            v-if="isChoice(editingQuestion?.question_type || '')"
            label="选项（JSON 对象，例如：A、B、C、D 对应选项文本）"
            ><el-input v-model="editForm.options" type="textarea" :rows="4"
          /></el-form-item>
          <el-form-item label="答案"
            ><el-input v-model="editForm.answer" type="textarea" :rows="3"
          /></el-form-item>
          <el-form-item label="解析"
            ><el-input v-model="editForm.explanation" type="textarea" :rows="5"
          /></el-form-item>
          <el-form-item
            :label="
              editingQuestion?.require_illustration
                ? '配图（本题要求配图）'
                : '配图（可选）'
            "
            ><div class="image-controls">
              <input
                ref="fileInput"
                class="file-input"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                aria-label="选择替换配图"
                @change="selectImage"
              /><el-button @click="fileInput?.click()">选择替换配图</el-button
              ><el-button
                v-if="editForm.illustration_url"
                type="danger"
                plain
                @click="removeEditImage"
                >移除当前配图</el-button
              ><span class="question-meta">PNG / JPG / WebP，不超过 2 MB</span>
            </div></el-form-item
          >
        </el-form>
        <div class="editor-preview">
          <div class="preview-heading">
            实时预览 <el-tag size="small" type="info">尚未保存</el-tag>
          </div>
          <h3>{{ editForm.title || '未命名草稿' }}</h3>
          <QuestionPreview :question="editPreview" :reveal="true" />
        </div>
      </div>
      <template #footer
        ><el-button @click="cancelEdit">取消修改</el-button
        ><el-button type="primary" :loading="saving" @click="saveEdit"
          >保存为新版本</el-button
        ></template
      >
    </el-dialog>
    <el-dialog
      v-model="ratingVisible"
      title="我的评分与评价"
      width="min(520px, 94vw)"
      ><el-form label-position="top"
        ><el-form-item label="评分"
          ><el-rate v-model="ratingForm.rating" show-text /></el-form-item
        ><el-form-item label="教学评价"
          ><el-input
            v-model="ratingForm.comment"
            type="textarea"
            :rows="4"
            maxlength="1000"
            show-word-limit
            placeholder="记录题目质量与课堂使用建议" /></el-form-item></el-form
      ><template #footer
        ><el-button @click="ratingVisible = false">取消</el-button
        ><el-button type="primary" @click="saveRating"
          >保存评价</el-button
        ></template
      ></el-dialog
    >
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  View,
  Edit,
  Download,
  Delete,
  Plus,
} from '@element-plus/icons-vue'
import {
  prototypeState,
  getCurrentUser,
  updateDraft,
  confirmQuestion,
  removeQuestion,
  rateQuestionLocal,
  exportQuestions,
} from '@/prototype/store'
import type { PrototypeQuestion } from '@/prototype/types'
import { parseMarkdown } from '@/utils/markdown'
import QuestionPreview from './QuestionPreview.vue'

const router = useRouter()
const route = useRoute()
const filters = reactive({
  keyword: '',
  type: '',
  knowledge: '',
  bloom: '',
  status: '',
  thinking: '',
})
const sort = ref('newest')
const currentPage = ref(1)
const pageSize = ref(5)
const selectedIds = ref<number[]>([])
const typeLabels: Record<string, string> = {
  single_choice: '单选题',
  multiple_choice: '多选题',
  fill_blank: '填空题',
  short_answer: '简答题',
}
const bloomLabels: Record<string, string> = {
  remember: '记忆',
  understand: '理解',
  apply: '应用',
  analyze: '分析',
}
const thinkingLabels: Record<string, string> = {
  C1: '建模与多重表征',
  C2: '科学推理与定量分析',
  C3: '证据论证与科学解释',
  C4: '实验设计与数据评价',
  C5: '批判质疑与方案创新',
  C6: '迁移整合与真实问题解决',
}
const typeLabel = (value: string) => typeLabels[value.toLowerCase()] || value
const bloomLabel = (value: string) => bloomLabels[value.toLowerCase()] || value
const difficultyLabel = (value: string) =>
  ({ easy: '基础', medium: '中等', hard: '困难' })[value] || value
const statusLabel = (value: string) =>
  value === 'confirmed' ? '教师已确认' : '待教师人工审核'
const isChoice = (value: string) => value.toLowerCase().includes('choice')
const formatDate = (value: string) =>
  new Date(value).toLocaleString('zh-CN', { hour12: false })
const ownQuestions = computed(() =>
  prototypeState.questions.filter((q) => q.user_id === getCurrentUser()?.id),
)
const knowledgePoints = computed(() =>
  [...new Set(ownQuestions.value.map((q) => q.knowledge_point))].filter(
    Boolean,
  ),
)
const filteredQuestions = computed(() => {
  const keyword = filters.keyword.trim().toLowerCase()
  return ownQuestions.value
    .filter(
      (q) =>
        (!keyword ||
          `${q.title} ${q.content}`.toLowerCase().includes(keyword)) &&
        (!filters.type || q.question_type.toLowerCase() === filters.type) &&
        (!filters.knowledge || q.knowledge_point === filters.knowledge) &&
        (!filters.bloom || q.bloom_level.toLowerCase() === filters.bloom) &&
        (!filters.thinking || q.thinking_tags?.includes(filters.thinking)) &&
        (!filters.status || q.teacher_status === filters.status),
    )
    .sort((a, b) =>
      sort.value === 'rating'
        ? (b.rating || 0) - (a.rating || 0)
        : (new Date(b.created_at).getTime() -
            new Date(a.created_at).getTime()) *
          (sort.value === 'oldest' ? -1 : 1),
    )
})
const pageQuestions = computed(() =>
  filteredQuestions.value.slice(
    (currentPage.value - 1) * pageSize.value,
    currentPage.value * pageSize.value,
  ),
)
const allPageSelected = computed(
  () =>
    pageQuestions.value.length > 0 &&
    pageQuestions.value.every((q) => selectedIds.value.includes(q.id)),
)
const somePageSelected = computed(
  () =>
    !allPageSelected.value &&
    pageQuestions.value.some((q) => selectedIds.value.includes(q.id)),
)
watch(
  [filters, sort, pageSize],
  () => {
    currentPage.value = 1
  },
  { deep: true },
)
watch(
  () => filteredQuestions.value.length,
  (count) => {
    currentPage.value = Math.min(
      currentPage.value,
      Math.max(1, Math.ceil(count / pageSize.value)),
    )
  },
)
watch(ownQuestions, (items) => {
  selectedIds.value = selectedIds.value.filter((id) =>
    items.some((q) => q.id === id),
  )
})
watch(
  () => route.query.status,
  (raw) => {
    const value = Array.isArray(raw) ? raw[0] : raw
    filters.status = value === 'pending' || value === 'confirmed' ? value : ''
  },
  { immediate: true },
)
function resetFilters() {
  Object.assign(filters, {
    keyword: '',
    type: '',
    knowledge: '',
    bloom: '',
    status: '',
    thinking: '',
  })
  currentPage.value = 1
}
function toggleSelection(id: number, selected: boolean) {
  selectedIds.value = selected
    ? [...new Set([...selectedIds.value, id])]
    : selectedIds.value.filter((value) => value !== id)
}
function togglePageSelection(value: string | number | boolean) {
  pageQuestions.value.forEach((q) => toggleSelection(q.id, Boolean(value)))
}
function reportError(error: unknown) {
  ElMessage.error(error instanceof Error ? error.message : '操作未完成，请重试')
}

const detailVisible = ref(false)
const detailTab = ref('content')
const currentId = ref<number | null>(null)
const currentQuestion = computed(() =>
  ownQuestions.value.find((q) => q.id === currentId.value),
)
const currentConfirmation = computed(() =>
  currentQuestion.value?.confirmations.find(
    (c) => c.version === currentQuestion.value?.version,
  ),
)
function openDetail(question: PrototypeQuestion) {
  currentId.value = question.id
  detailTab.value = 'content'
  detailVisible.value = true
}
watch(
  () => route.query.question_id || route.query.id,
  (raw) => {
    const id = Number(Array.isArray(raw) ? raw[0] : raw)
    if (!Number.isFinite(id) || id < 1) return
    const question = ownQuestions.value.find((q) => q.id === id)
    if (question) openDetail(question)
    else ElMessage.warning('未找到本人题库中的该习题')
  },
  { immediate: true },
)

const editVisible = ref(false)
const editingId = ref<number | null>(null)
const editingQuestion = computed(() =>
  ownQuestions.value.find((q) => q.id === editingId.value),
)
const editForm = reactive({
  title: '',
  content: '',
  options: '',
  answer: '',
  explanation: '',
  illustration_url: '',
})
const editPreview = computed(() => ({
  ...editForm,
  require_illustration: editingQuestion.value?.require_illustration,
}))
const originalEdit = ref('')
const saving = ref(false)
const fileInput = ref<HTMLInputElement>()
function openEdit(question: PrototypeQuestion) {
  editingId.value = question.id
  Object.assign(editForm, {
    title: question.title,
    content: question.content,
    options: question.options || '',
    answer: question.answer,
    explanation: question.explanation || '',
    illustration_url: question.illustration_url || '',
  })
  originalEdit.value = JSON.stringify(editForm)
  editVisible.value = true
}
async function cancelEdit() {
  await beforeCloseEdit(() => {
    editVisible.value = false
  })
}
async function beforeCloseEdit(done: () => void) {
  if (JSON.stringify(editForm) !== originalEdit.value) {
    try {
      await ElMessageBox.confirm(
        '未保存的修改将被放弃。是否关闭编辑？',
        '放弃修改',
        {
          type: 'warning',
          confirmButtonText: '放弃修改',
          cancelButtonText: '继续编辑',
        },
      )
    } catch {
      return
    }
  }
  done()
}
async function selectImage(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
    ElMessage.error('请选择 PNG、JPG 或 WebP 图片')
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('图片不能超过 2 MB')
    return
  }
  try {
    const url = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(String(reader.result))
      reader.onerror = () => reject(new Error('图片读取失败'))
      reader.readAsDataURL(file)
    })
    await verifyImage(url)
    editForm.illustration_url = url
    ElMessage.success('已加载配图，请核对右侧预览后保存')
  } catch (error) {
    reportError(error)
  }
}
function removeEditImage() {
  editForm.illustration_url = ''
}
async function saveEdit() {
  if (!editingId.value) return
  if (JSON.stringify(editForm) === originalEdit.value) {
    ElMessage.info('尚未修改内容')
    return
  }
  if (editForm.options.trim()) {
    try {
      const options: unknown = JSON.parse(editForm.options)
      if (
        !options ||
        typeof options !== 'object' ||
        Array.isArray(options) ||
        !Object.values(options).every((value) => typeof value === 'string')
      )
        throw new Error()
    } catch {
      ElMessage.error('选项须为 JSON 对象，且每个选项的内容须为文本')
      return
    }
  }
  saving.value = true
  try {
    updateDraft(editingId.value, { ...editForm })
    editVisible.value = false
    ElMessage.success('新版本已保存，待教师人工审核并确认定稿')
  } catch (error) {
    reportError(error)
  } finally {
    saving.value = false
  }
}
function verifyImage(url: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    const timer = window.setTimeout(() => {
      image.onload = image.onerror = null
      reject(new Error('配图无法预览，请替换为可正常读取的图片'))
    }, 6000)
    image.onload = () => {
      clearTimeout(timer)
      image.naturalWidth > 0
        ? resolve()
        : reject(new Error('配图为空，请重新上传'))
    }
    image.onerror = () => {
      clearTimeout(timer)
      reject(new Error('配图无法预览，请先替换图片再确认定稿'))
    }
    image.src = url
  })
}
const confirming = ref(false)
async function confirmCurrent(question: PrototypeQuestion) {
  if (confirming.value) return
  const approvedVersion = question.version
  confirming.value = true
  try {
    try {
      await ElMessageBox.confirm(
        `确认已人工核验「${question.title || '未命名草稿'}」的题干、选项、答案、解析和配图，并将当前 v${approvedVersion} 确认定稿？`,
        '教师确认定稿',
        {
          type: 'warning',
          confirmButtonText: '确认当前版本定稿',
          cancelButtonText: '返回继续审核',
        },
      )
    } catch {
      return
    }
    if (question.illustration_url) await verifyImage(question.illustration_url)
    const latest = ownQuestions.value.find((q) => q.id === question.id)
    if (!latest || latest.version !== approvedVersion)
      throw new Error('题目内容已发生变化，请核验新版本后重新确认')
    confirmQuestion(question.id)
    ElMessage.success(`v${approvedVersion} 已由教师确认，可导出定稿`)
  } catch (error) {
    reportError(error)
  } finally {
    confirming.value = false
  }
}
async function deleteCurrent(question: PrototypeQuestion) {
  try {
    await ElMessageBox.confirm(
      `确定删除「${question.title || '未命名草稿'}」？其版本、配图关联和确认记录将一并移除。`,
      '删除习题',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
      },
    )
  } catch {
    return
  }
  try {
    removeQuestion(question.id)
    if (currentId.value === question.id) detailVisible.value = false
    ElMessage.success('习题已删除')
  } catch (error) {
    reportError(error)
  }
}
function exportOne(id: number) {
  try {
    exportQuestions([id])
    ElMessage.success('已导出定稿 TXT')
  } catch (error) {
    reportError(error)
  }
}
function exportSelected() {
  const selected = ownQuestions.value.filter((q) =>
    selectedIds.value.includes(q.id),
  )
  if (selected.some((q) => q.teacher_status !== 'confirmed')) {
    ElMessage.warning('选中题目含待教师人工审核的草稿，请先逐题确认定稿')
    return
  }
  try {
    exportQuestions(selectedIds.value)
    ElMessage.success(`已导出 ${selected.length} 道定稿`)
  } catch (error) {
    reportError(error)
  }
}
const ratingVisible = ref(false)
const ratingId = ref<number | null>(null)
const ratingForm = reactive({ rating: 0, comment: '' })
function openRating(question: PrototypeQuestion) {
  ratingId.value = question.id
  ratingForm.rating = question.rating || 0
  ratingForm.comment = question.comment || ''
  ratingVisible.value = true
}
function saveRating() {
  if (ratingId.value === null) return
  try {
    rateQuestionLocal(ratingId.value, ratingForm.rating, ratingForm.comment)
    ratingVisible.value = false
    ElMessage.success('评分与评价已保存')
  } catch (error) {
    reportError(error)
  }
}
</script>

<style scoped>
.question-manage-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.thinking-filter-row,
.thinking-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  color: #72809b;
  font-size: 12px;
  margin-top: 14px;
}
.thinking-filter-row .export-hint {
  margin-top: 0;
}
.page-header,
.list-toolbar,
.question-footer,
.detail-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.title-section {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
.title-section h2 {
  font-size: 24px;
}
.subtitle {
  color: var(--color-text-secondary);
  font-size: 14px;
}
.summary-row {
  display: flex;
  flex-wrap: wrap;
  gap: 30px;
  border-top: 1px solid #edf2fa;
  padding-top: 18px;
  margin-top: 20px;
  color: #72809b;
}
.summary-row strong {
  margin-left: 7px;
  color: #1f2a44;
  font-size: 22px;
}
.filter-bar {
  display: grid;
  grid-template-columns: minmax(190px, 2fr) repeat(4, minmax(125px, 1fr)) auto;
  gap: 12px;
}
.filter-bar :deep(.el-select) {
  width: 100%;
}
.list-toolbar {
  margin-top: 20px;
}
.selection-tools,
.rating-section,
.action-section,
.question-tags,
.image-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}
.selection-tools,
.export-hint,
.rating-section {
  font-size: 13px;
  color: #7b87a6;
}
.export-hint {
  margin-top: 12px;
}
.question-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.question-item {
  padding: 22px;
  border: 1px solid #e5ecf8;
  border-radius: 12px;
  background: #fff;
  transition: box-shadow 0.2s;
}
.question-item:hover {
  box-shadow: 0 7px 20px #5281bf12;
  border-color: #b9d2ff;
}
.question-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}
.question-heading {
  flex: 1;
  min-width: 0;
}
.question-heading h3 {
  margin: 12px 0 8px;
  font-size: 17px;
  font-weight: 600;
  line-height: 1.6;
}
.question-meta {
  color: #8791a6;
  font-size: 12px;
  line-height: 1.8;
}
.content-preview {
  line-height: 1.9;
  margin: 18px 0;
  padding: 15px 18px;
  background: #f8faff;
  border-radius: 8px;
  max-height: 145px;
  overflow: hidden;
  color: #45536d;
}
.content-preview :deep(p) {
  margin: 0;
}
.question-footer {
  border-top: 1px solid #eef2f8;
  padding-top: 14px;
}
.action-section :deep(.el-button + .el-button) {
  margin-left: 0;
}
.comment-section {
  margin-top: 12px;
  padding: 10px 14px;
  background: #fff9ed;
  border-radius: 7px;
  font-size: 13px;
  line-height: 1.7;
  overflow-wrap: anywhere;
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 25px;
  overflow-x: auto;
}
.detail-heading {
  margin-bottom: 10px;
}
.detail-heading h2 {
  font-size: 21px;
}
.detail-content :deep(.el-alert) {
  margin: 10px 0 18px;
}
.confirmation-record {
  padding: 14px;
  background: #eff9ed;
  color: #468639;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.8;
  margin-top: 18px;
}
.evidence-card {
  margin: 15px 0;
  border: 1px solid #e8eef8;
  padding: 20px;
  border-radius: 10px;
}
.evidence-text {
  margin-top: 12px;
  line-height: 1.9;
  color: #526078;
  white-space: pre-wrap;
}
.version-title {
  padding-right: 15px;
  color: #526078;
}
.editor-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px;
  margin-top: 22px;
  align-items: start;
}
.editor-form {
  min-width: 0;
}
.editor-form :deep(.el-form-item__label) {
  font-weight: 500;
}
.editor-preview {
  padding: 22px;
  border: 1px solid #e5ecf8;
  border-radius: 12px;
  background: #f9fbff;
  min-width: 0;
  position: sticky;
  top: 0;
  max-height: 70vh;
  overflow-y: auto;
}
.preview-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #7b87a6;
  margin-bottom: 20px;
}
.editor-preview > h3 {
  line-height: 1.7;
  margin-bottom: 18px;
}
.file-input {
  display: none;
}
@media (max-width: 1200px) {
  .filter-bar {
    grid-template-columns: repeat(3, minmax(130px, 1fr));
  }
}
@media (max-width: 800px) {
  .editor-layout {
    grid-template-columns: 1fr;
  }
  .editor-preview {
    position: static;
  }
  .filter-bar {
    grid-template-columns: repeat(2, minmax(110px, 1fr));
  }
  .question-item {
    padding: 15px;
  }
  .summary-row {
    gap: 15px;
  }
  .title-section .subtitle {
    width: 100%;
  }
}
</style>
