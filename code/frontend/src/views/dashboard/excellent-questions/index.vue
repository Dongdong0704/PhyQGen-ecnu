<template>
  <div class="excellent-page">
    <!-- 页头 -->
    <el-card class="header-card">
      <div class="page-header">
        <div class="title-section">
          <el-tag class="title-badge" type="warning" effect="dark"
            >优秀习题</el-tag
          >
          <h2>优秀习题广场</h2>
          <span class="subtitle">由教师确认且评分达到 4 分的习题</span>
        </div>
        <div class="action-section">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索标题或题干"
            clearable
            maxlength="500"
            aria-label="搜索习题"
            class="search-input"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
            :prefix-icon="Search"
          />
          <el-button class="search-btn" type="primary" @click="handleSearch">
            <Search style="margin-right: 5px" />
            搜索
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 筛选排序栏 -->
    <el-card class="filter-card">
      <div class="filter-bar">
        <div class="filter-group">
          <span class="filter-label">排序：</span>
          <el-select
            v-model="sortBy"
            @change="resetPage"
            style="width: 160px"
          >
            <el-option label="创建时间" value="created_at" />
            <el-option label="教师评分" value="max_rating" />
          </el-select>
          <el-select
            v-model="sortOrder"
            @change="resetPage"
            style="width: 120px; margin-left: 10px"
          >
            <el-option label="降序" value="desc" />
            <el-option label="升序" value="asc" />
          </el-select>
        </div>
        <div class="total-info">
          共 <strong>{{ total }}</strong> 道优秀习题
        </div>
      </div>
    </el-card>

    <!-- 列表 -->
    <el-card class="list-card" v-loading="loading">
      <div v-if="listError" class="load-error" role="alert">
        <span>{{ listError }}</span>
        <el-button text type="primary" @click="loadQuestions">重试</el-button>
      </div>
      <el-empty
        v-else-if="!loading && questionList.length === 0"
        :image-size="120"
        :description="appliedKeyword ? '没有匹配的优秀习题' : '暂无教师已确认且评分达到 4 分的习题'"
      />

      <div v-else class="question-list">
        <div v-for="item in questionList" :key="item.id" class="question-item">
          <div class="question-header">
            <div class="question-title">
              <el-tag size="small" :type="getTypeColor(item.question_type)">{{
                getTypeLabel(item.question_type)
              }}</el-tag>
              <el-tag
                size="small"
                :type="getBloomLevelType(item.bloom_level)"
                >{{ getBloomLevelText(item.bloom_level) }}</el-tag
              >
              <el-tag
                v-if="item.has_illustration"
                size="small"
                type="success"
                effect="plain"
                class="illustration-flag"
              >
                <el-icon><Picture /></el-icon>配图
              </el-tag>
              <span class="title-text">{{ item.title }}</span>
            </div>
            <div class="question-meta">
              <span class="meta-item rating-badge">
                <el-icon><StarFilled /></el-icon>教师评分
                {{ item.max_teacher_rating }} 分
              </span>
              <span class="meta-item"
                ><el-icon><Calendar /></el-icon
                >{{ formatDate(item.created_at) }}</span
              >
              <span class="meta-item"
                ><el-icon><Document /></el-icon>{{ item.grade }}</span
              >
            </div>
          </div>

          <div class="question-content">
            <div class="content-preview markdown-body" v-html="parseMarkdown(item.content)" />
          </div>

          <div class="question-footer">
            <div class="action-section">
              <el-button size="small" @click="openDiscussion(item)">
                <el-icon><ChatDotRound /></el-icon>讨论区
              </el-button>
              <el-button type="primary" size="small" @click="showDetail(item)">
                <el-icon><View /></el-icon>详情
              </el-button>
              <el-button
                type="success"
                size="small"
                :loading="downloading.has(item.id)"
                @click="handleDownload(item)"
              >
                <el-icon><Download /></el-icon>下载
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="pagination-wrapper" v-if="!listError && total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @update:page-size="updatePageSize"
        />
      </div>
    </el-card>
  </div>

  <!-- 详情弹窗 -->
  <el-dialog
    v-model="detailVisible"
    title="习题详情"
    width="min(800px, 94vw)"
    :close-on-click-modal="false"
  >
    <el-skeleton v-if="detailLoading" :rows="5" animated />
    <div v-else-if="detailError" class="load-error" role="alert">
      <span>{{ detailError }}</span>
      <el-button v-if="!detailUnavailable" text type="primary" @click="loadDetail">重试</el-button>
    </div>
    <div v-else-if="currentQuestion" class="detail-content">
      <div class="detail-header">
        <el-tag
          size="default"
          :type="getTypeColor(currentQuestion.question_type)"
          >{{ getTypeLabel(currentQuestion.question_type) }}</el-tag
        >
        <el-tag
          size="default"
          :type="getBloomLevelType(currentQuestion.bloom_level)"
          >{{ getBloomLevelText(currentQuestion.bloom_level) }}</el-tag
        >
        <el-tag size="default" type="warning" effect="plain">
          <el-icon style="margin-right: 2px"><StarFilled /></el-icon>教师评分
          {{ currentQuestion.max_teacher_rating }} 分
        </el-tag>
        <span class="detail-title">{{ currentQuestion.title }}</span>
      </div>

      <div class="detail-section">
        <div class="section-title">教学属性与确认记录</div>
        <div class="section-content">
          <p>
            {{ currentQuestion.grade }} · 知识点：{{ currentQuestion.knowledge_point || '未记录' }} ·
            目标难度：{{ difficultyLabel(currentQuestion.difficulty) }}
          </p>
          <p>高阶思维能力：{{ thinkingText(currentQuestion.thinking_tags) }}</p>
          <p>教师已确认 · v{{ currentQuestion.version || 1 }}</p>
          <p
            v-for="record in currentQuestion.confirmations?.filter(
              (c) => c.version === currentQuestion?.version,
            ) || []"
            :key="record.confirmed_at"
          >
            确认人：{{ record.teacher_name }} ·
            {{ formatDate(record.confirmed_at) }}
          </p>
        </div>
      </div>
      <div class="detail-section">
        <div class="section-title">习题内容</div>
        <div
          class="section-content markdown-body"
          v-html="parseMarkdown(currentQuestion.content)"
        />
      </div>

      <div class="detail-section" v-if="currentQuestion.options">
        <div class="section-title">选项</div>
        <div class="section-content">
          <div v-if="parsedOptions" class="options-list">
            <div
              v-for="(optionText, optionKey) in parsedOptions"
              :key="optionKey"
              class="option-item"
            >
              <span class="option-key">{{ optionKey }}.</span>
              <div
                class="option-text markdown-body"
                v-html="parseMarkdown(optionText)"
              />
            </div>
          </div>
          <div v-else class="markdown-body" v-html="parseMarkdown(currentQuestion.options)" />
        </div>
      </div>

      <div class="detail-section" v-if="currentQuestion.illustration_url">
        <div class="section-title">配图</div>
        <div class="section-content">
          <img
            :src="getFullImageUrl(currentQuestion.illustration_url)"
            alt="习题配图"
            class="illustration-image"
          />
        </div>
      </div>

      <div class="detail-section">
        <div class="section-title-with-btn">
          <span class="section-title">答案</span>
          <el-button type="info" size="small" @click="toggleAnswerVisibility">
            <el-icon><View v-if="!showAnswer" /><Hide v-else /></el-icon>
            {{ showAnswer ? '隐藏答案' : '显示答案' }}
          </el-button>
        </div>
        <div
          v-if="showAnswer"
          class="section-content answer-content markdown-body"
          v-html="parseMarkdown(currentQuestion.answer)"
        />
      </div>

      <div class="detail-section" v-if="currentQuestion.explanation">
        <div class="section-title-with-btn">
          <span class="section-title">解析</span>
          <el-button
            type="info"
            size="small"
            @click="toggleExplanationVisibility"
          >
            <el-icon><View v-if="!showExplanation" /><Hide v-else /></el-icon>
            {{ showExplanation ? '隐藏解析' : '显示解析' }}
          </el-button>
        </div>
        <div
          v-if="showExplanation"
          class="section-content explanation-content markdown-body"
          v-html="parseMarkdown(currentQuestion.explanation)"
        />
      </div>
      <div class="detail-section">
        <div class="section-title">引用来源</div>
        <div class="section-content">
          <div
            v-for="evidence in currentQuestion.evidence || []"
            :key="evidence.fragment_id"
            style="margin-bottom: 10px"
          >
            <strong>{{ evidence.source }}</strong>
            <p>
              片段 {{ evidence.fragment_id }} · 索引
              {{ evidence.index_version }}
            </p>
            <p>{{ evidence.content }}</p>
          </div>
          <p v-if="!currentQuestion.evidence?.length">
            {{ currentQuestion.kb_reason || '本题未记录知识库引用' }}
          </p>
        </div>
      </div>
    </div>
    <template #footer>
      <el-button @click="detailVisible = false">关闭</el-button>
      <el-button
        v-if="currentQuestion"
        type="success"
        :loading="downloading.has(currentQuestion.id)"
        @click="handleDownload(currentQuestion)"
      >
        <el-icon><Download /></el-icon>下载习题
      </el-button>
    </template>
  </el-dialog>

  <QuestionDiscussionDrawer
    v-model="discussionDrawerVisible"
    :question="discussionQuestion"
    @unavailable="loadQuestions"
  />
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  Calendar,
  Document,
  View,
  Hide,
  Download,
  StarFilled,
  ChatDotRound,
  Picture,
} from '@element-plus/icons-vue'
import { HttpError } from '@/api/http'
import {
  getExcellentQuestion,
  getExcellentQuestions,
  type ExcellentQuestion,
  type ExcellentQuestionDetail,
  type ExcellentSort,
  type SortOrder,
} from '@/api/modules/excellent-questions'
import { parseMarkdown } from '@/utils/markdown'
import QuestionDiscussionDrawer from './QuestionDiscussionDrawer.vue'
import {
  difficultyLabel,
  downloadExcellentQuestion,
  formatDate,
  getBloomLevelText,
  getBloomLevelType,
  getFullImageUrl,
  getTypeColor,
  getTypeLabel,
  parseOptions,
  thinkingText,
} from './presentation'

const loading = ref(false)
const listError = ref('')
const questionList = ref<ExcellentQuestion[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchKeyword = ref('')
const appliedKeyword = ref('')
const sortBy = ref<ExcellentSort>('created_at')
const sortOrder = ref<SortOrder>('desc')
let listRequest = 0

const detailVisible = ref(false)
const detailSelection = ref<ExcellentQuestion | null>(null)
const currentQuestion = ref<ExcellentQuestionDetail | null>(null)
const detailLoading = ref(false)
const detailError = ref('')
const detailUnavailable = ref(false)
const showAnswer = ref(false)
const showExplanation = ref(false)
const parsedOptions = computed(() => parseOptions(currentQuestion.value?.options))
let detailRequest = 0

const discussionDrawerVisible = ref(false)
const discussionQuestion = ref<ExcellentQuestion | null>(null)
const downloading = reactive(new Set<number>())

watch([currentPage, pageSize, appliedKeyword, sortBy, sortOrder], () => void loadQuestions(), {
  immediate: true,
})
watch(detailVisible, (visible) => {
  if (!visible) detailRequest++
})
onBeforeUnmount(() => {
  listRequest++
  detailRequest++
})

async function loadQuestions() {
  const request = ++listRequest
  const page = currentPage.value
  const size = pageSize.value
  loading.value = true
  listError.value = ''
  try {
    const result = await getExcellentQuestions({
      page,
      page_size: size,
      keyword: appliedKeyword.value || undefined,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
    })
    if (request !== listRequest) return
    total.value = result.total
    const lastPage = Math.max(1, Math.ceil(result.total / size))
    if (page > lastPage) {
      currentPage.value = lastPage
      return
    }
    questionList.value = result.items
  } catch (error) {
    if (request === listRequest) listError.value = messageFor(error, '加载优秀习题失败')
  } finally {
    if (request === listRequest) loading.value = false
  }
}

function resetPage() {
  currentPage.value = 1
}

function updatePageSize(size: number) {
  pageSize.value = size
  resetPage()
}

function handleSearch() {
  const keyword = searchKeyword.value.trim()
  const sameQuery = keyword === appliedKeyword.value && currentPage.value === 1
  appliedKeyword.value = keyword
  resetPage()
  if (sameQuery) void loadQuestions()
}

function showDetail(item: ExcellentQuestion) {
  detailSelection.value = item
  detailVisible.value = true
  void loadDetail()
}

async function loadDetail() {
  const selected = detailSelection.value
  if (!selected || !detailVisible.value) return

  const request = ++detailRequest
  currentQuestion.value = null
  detailLoading.value = true
  detailError.value = ''
  detailUnavailable.value = false
  showAnswer.value = false
  showExplanation.value = false
  try {
    const detail = await getExcellentQuestion(selected.id)
    if (detailVisible.value && request === detailRequest) currentQuestion.value = detail
  } catch (error) {
    if (!detailVisible.value || request !== detailRequest) return
    detailUnavailable.value = notFound(error)
    detailError.value = messageFor(error, '加载习题详情失败')
    if (detailUnavailable.value) void loadQuestions()
  } finally {
    if (detailVisible.value && request === detailRequest) detailLoading.value = false
  }
}

function toggleAnswerVisibility() {
  showAnswer.value = !showAnswer.value
}
function toggleExplanationVisibility() {
  showExplanation.value = !showExplanation.value
}

function openDiscussion(item: ExcellentQuestion) {
  discussionQuestion.value = item
  discussionDrawerVisible.value = true
}

async function handleDownload(item: ExcellentQuestion) {
  if (downloading.has(item.id)) return

  const request = detailRequest
  const isSameDetail = () =>
    detailVisible.value && detailSelection.value?.id === item.id && request === detailRequest

  downloading.add(item.id)
  try {
    const current = await getExcellentQuestion(item.id)
    if (item.version !== current.version) {
      ElMessage.warning('习题版本已更新，请核对当前定稿后重新下载')
      if (isSameDetail()) {
        currentQuestion.value = current
        showAnswer.value = false
        showExplanation.value = false
      }
      void loadQuestions()
      return
    }

    downloadExcellentQuestion(current)
    ElMessage.success('下载成功')
  } catch (error) {
    const message = messageFor(error, '下载失败')
    ElMessage.error(message)
    if (notFound(error)) {
      if (isSameDetail()) {
        currentQuestion.value = null
        detailUnavailable.value = true
        detailError.value = message
      }
      void loadQuestions()
    }
  } finally {
    downloading.delete(item.id)
  }
}

function notFound(error: unknown) {
  return error instanceof HttpError && error.status === 404
}
function messageFor(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback
}
</script>

<style scoped>
/* ─────────────── 页面基础 ─────────────── */
.excellent-page {
  padding: 0;
  background-color: transparent;
  height: 100%;
  overflow-y: auto;
}

.header-card {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #fffbf0 0%, #fff8e1 100%);
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}
.title-badge {
  margin-bottom: 10px;
  border-radius: 999px;
}
.page-header .title-section h2 {
  margin: 0 0 5px 0;
  font-size: 24px;
  color: var(--color-text-primary);
}
.page-header .title-section .subtitle {
  color: var(--color-text-secondary);
  font-size: 14px;
}
.page-header .action-section {
  display: flex;
  gap: 10px;
}
.search-input {
  width: 300px;
}

.filter-card {
  margin-bottom: 20px;
}
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.filter-group {
  display: flex;
  align-items: center;
}
.filter-label {
  color: var(--color-text-regular);
  margin-right: 10px;
}
.total-info {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.list-card .question-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.question-item {
  border: 1px solid #f0e6c8;
  border-radius: 12px;
  padding: 20px;
  background: linear-gradient(180deg, #ffffff 0%, #fffdf7 100%);
  transition: all 0.3s;
}
.question-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(230, 162, 60, 0.14);
}
.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.question-title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}
.question-title .title-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}
.illustration-flag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.question-meta {
  display: flex;
  gap: 16px;
  color: var(--color-text-secondary);
  font-size: 14px;
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.rating-badge {
  color: #e6a23c;
  font-weight: 600;
}
.question-content {
  margin-bottom: 16px;
  padding: 15px;
  background: #fafaf7;
  border-radius: 10px;
}
.question-content .content-preview :deep(img) {
  max-width: 100%;
}
.question-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
}
.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  overflow-x: auto;
}

.load-error {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  color: var(--el-color-danger);
  background: var(--el-color-danger-light-9);
  border-radius: 8px;
}

/* ─────────────── 详情弹窗 ─────────────── */
.detail-content {
  max-height: 70vh;
  overflow-y: auto;
}
.detail-header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0e6c8;
}
.detail-header .detail-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}
.detail-section {
  margin-bottom: 20px;
}
.detail-section .section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}
.detail-section .section-title-with-btn {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.section-content {
  padding: 12px 16px;
  background: #fafaf7;
  border-radius: 8px;
  line-height: 1.8;
}
.answer-content {
  background: #f0faf4;
  border-left: 4px solid #67c23a;
}
.explanation-content {
  background: #f5f7ff;
  border-left: 4px solid #409eff;
}
.options-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.option-item {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.option-key {
  font-weight: 600;
  min-width: 20px;
}
.illustration-image {
  max-width: 100%;
  border-radius: 8px;
}

@media (max-width: 760px) {
  .page-header,
  .question-header,
  .filter-bar {
    flex-wrap: wrap;
  }
  .page-header .action-section {
    width: 100%;
  }
  .search-input {
    flex: 1;
    min-width: 0;
  }
  .question-header {
    gap: 8px;
  }
  .question-meta {
    flex-wrap: wrap;
  }
  .filter-bar {
    gap: 10px;
  }
  .pagination-wrapper {
    justify-content: flex-start;
  }
}
</style>
