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
          <span class="subtitle"
            >保留原系统的优秀习题与讨论功能，展示教师已确认且评分 ≥ 4
            分的题目</span
          >
        </div>
        <div class="action-section">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索习题..."
            clearable
            style="width: 300px"
            @keyup.enter="handleSearch"
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
            @change="loadQuestions"
            style="width: 160px"
          >
            <el-option label="创建时间" value="created_at" />
            <el-option label="教师最高评分" value="max_rating" />
          </el-select>
          <el-select
            v-model="sortOrder"
            @change="loadQuestions"
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
      <el-empty v-if="!loading && questionList.length === 0" :image-size="120">
        <template #description>
          <p style="color: #909399">
            还没有教师评分达到 4 分的习题，快去生成并评分吧~
          </p>
        </template>
      </el-empty>

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
                v-if="item.illustration_url"
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
            <div class="content-preview" v-html="parseMarkdown(item.content)" />
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
                @click="handleDownload(item)"
              >
                <el-icon><Download /></el-icon>下载
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="pagination-wrapper" v-if="total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadQuestions"
          @current-change="loadQuestions"
        />
      </div>
    </el-card>
  </div>

  <!-- 详情弹窗 -->
  <el-dialog
    v-model="detailVisible"
    title="习题详情"
    width="800px"
    :close-on-click-modal="false"
  >
    <div v-if="currentQuestion" class="detail-content">
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
            知识点：{{ currentQuestion.knowledge_point || '未记录' }} ·
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
          class="section-content"
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
              <span
                class="option-text"
                v-html="parseMarkdown(optionText)"
              ></span>
            </div>
          </div>
          <div v-else v-html="parseMarkdown(currentQuestion.options)" />
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
          class="section-content answer-content"
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
          class="section-content explanation-content"
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
      <el-button type="success" @click="handleDownload(currentQuestion!)">
        <el-icon><Download /></el-icon>下载习题
      </el-button>
    </template>
  </el-dialog>

  <!-- 讨论区抽屉 -->
  <el-drawer
    v-model="discussionDrawerVisible"
    direction="rtl"
    size="62%"
    :with-header="false"
    class="discussion-drawer"
    @closed="onDrawerClosed"
  >
    <div class="drawer-inner">
      <!-- 抽屉头部 -->
      <div class="drawer-header">
        <div class="drawer-header-left">
          <el-icon class="header-icon"><ChatDotRound /></el-icon>
          <div>
            <div class="drawer-title">讨论区</div>
            <div class="drawer-subtitle" v-if="discussionQuestion">
              {{ discussionQuestion.title }}
            </div>
          </div>
        </div>
        <el-button circle text @click="discussionDrawerVisible = false">
          <el-icon :size="18"><Close /></el-icon>
        </el-button>
      </div>

      <!-- 讨论列表 -->
      <div class="discussion-list-wrap" ref="discussionListRef">
        <div
          v-if="discussionLoading && discussions.length === 0"
          class="disc-loading"
        >
          <el-skeleton :rows="5" animated />
        </div>
        <el-empty
          v-else-if="!discussionLoading && discussions.length === 0"
          description="暂无讨论，快来发表第一条~"
          :image-size="80"
        />

        <div v-else class="discussion-list">
          <!-- 顶层讨论 -->
          <div v-for="disc in discussions" :key="disc.id" class="disc-thread">
            <!-- 顶层条目 -->
            <div
              class="disc-item disc-top"
              :class="{ 'disc-mine': disc.user_id === currentUserId }"
            >
              <!-- 顶层标记 -->
              <div class="disc-type-badge">
                <el-icon><ChatDotRound /></el-icon>
                <span>讨论</span>
              </div>
              <div class="disc-main-row">
                <div class="disc-avatar" :class="getRoleClass(disc.role)">
                  {{ disc.username.charAt(0).toUpperCase() }}
                </div>
                <div class="disc-body">
                  <div class="disc-meta">
                    <span class="disc-username">{{ disc.username }}</span>
                    <el-tag
                      size="small"
                      :type="disc.role === 'TEACHER' ? 'warning' : 'info'"
                      effect="plain"
                      class="role-tag"
                    >
                      {{ roleLabel(disc.role) }}
                    </el-tag>
                    <span class="disc-time">{{
                      formatDate(disc.created_at)
                    }}</span>
                  </div>
                  <div class="disc-content">{{ disc.content }}</div>
                  <div class="disc-actions">
                    <el-button
                      text
                      size="small"
                      class="reply-btn"
                      @click="startReply(disc)"
                    >
                      <el-icon><ChatLineRound /></el-icon> 回复
                    </el-button>
                  </div>
                </div>
                <el-button
                  v-if="canDelete(disc)"
                  class="disc-delete-btn"
                  size="small"
                  text
                  type="danger"
                  @click="handleDeleteDiscussion(disc.id, false)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>

            <!-- 回复列表 -->
            <div
              v-if="disc.replies && disc.replies.length > 0"
              class="replies-wrap"
            >
              <div class="replies-thread-line" />
              <div class="replies-list">
                <div
                  v-for="reply in disc.replies"
                  :key="reply.id"
                  class="disc-item reply-item"
                  :class="{ 'disc-mine': reply.user_id === currentUserId }"
                >
                  <!-- 回复头部标记行 -->
                  <div class="reply-header-bar">
                    <el-icon class="reply-arrow-icon"><Right /></el-icon>
                    <span class="reply-label">回复了</span>
                    <span class="reply-to-name"
                      >@{{ reply.reply_to_username }}</span
                    >
                  </div>
                  <!-- 回复主体 -->
                  <div class="disc-main-row">
                    <div
                      class="disc-avatar disc-avatar-sm"
                      :class="getRoleClass(reply.role)"
                    >
                      {{ reply.username.charAt(0).toUpperCase() }}
                    </div>
                    <div class="disc-body">
                      <div class="disc-meta">
                        <span class="disc-username">{{ reply.username }}</span>
                        <el-tag
                          size="small"
                          :type="reply.role === 'TEACHER' ? 'warning' : 'info'"
                          effect="plain"
                          class="role-tag"
                        >
                          {{ roleLabel(reply.role) }}
                        </el-tag>
                        <span class="disc-time">{{
                          formatDate(reply.created_at)
                        }}</span>
                      </div>
                      <div class="disc-content">{{ reply.content }}</div>
                      <div class="disc-actions">
                        <el-button
                          text
                          size="small"
                          class="reply-btn"
                          @click="startReply(disc, reply)"
                        >
                          <el-icon><ChatLineRound /></el-icon> 回复
                        </el-button>
                      </div>
                    </div>
                    <el-button
                      v-if="canDelete(reply)"
                      class="disc-delete-btn"
                      size="small"
                      text
                      type="danger"
                      @click="handleDeleteDiscussion(reply.id, true, disc.id)"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 内联回复框（挂在当前顶层下） -->
            <div v-if="replyTarget?.topId === disc.id" class="inline-reply-box">
              <!-- 引用块：显示被回复的原文 -->
              <div class="reply-quote">
                <div class="reply-quote-from">
                  <el-icon><ChatLineRound /></el-icon>
                  正在回复
                  <strong class="reply-quote-name"
                    >@{{ replyTarget.toUsername }}</strong
                  >
                </div>
                <div class="reply-quote-text">
                  {{ replyTarget.previewText }}
                </div>
              </div>
              <div class="inline-reply-input-row">
                <el-input
                  v-model="replyContent"
                  type="textarea"
                  :rows="2"
                  :placeholder="`说点什么...`"
                  maxlength="2000"
                  resize="none"
                  class="disc-textarea"
                />
              </div>
              <div class="inline-reply-actions">
                <el-button text size="small" @click="cancelReply"
                  >取消</el-button
                >
                <el-button
                  type="primary"
                  size="small"
                  class="inline-send-btn"
                  :loading="submitting"
                  :disabled="!replyContent.trim()"
                  @click="handlePostReply"
                >
                  <el-icon><Promotion /></el-icon> 发送回复
                </el-button>
              </div>
            </div>
          </div>

          <!-- 加载更多 -->
          <div v-if="hasMoreDiscs" class="load-more">
            <el-button
              text
              :loading="discussionLoading"
              @click="loadMoreDiscussions"
              >加载更多</el-button
            >
          </div>
        </div>
      </div>

      <!-- 底部：发新讨论 -->
      <div
        class="disc-input-area"
        :class="{ 'is-replying-mode': !!replyTarget }"
      >
        <div class="disc-input-label-row">
          <div class="disc-input-label">发表新讨论</div>
          <el-tag v-if="replyTarget" type="warning" effect="light" round
            >当前处于回复模式</el-tag
          >
        </div>
        <div v-if="replyTarget" class="reply-mode-tip">
          正在回复 <strong>@{{ replyTarget.toUsername }}</strong
          >，如需发新讨论请先取消回复。
        </div>
        <div class="disc-input-wrap">
          <el-input
            v-model="newDiscContent"
            type="textarea"
            :rows="3"
            :placeholder="
              replyTarget
                ? '请先取消回复模式，再发表新讨论'
                : '分享你的想法、疑问或解题思路...'
            "
            maxlength="2000"
            show-word-limit
            resize="none"
            :disabled="!!replyTarget"
            class="disc-textarea"
          />
          <el-button
            type="primary"
            class="disc-submit-btn"
            :loading="submitting"
            :disabled="!!replyTarget || !newDiscContent.trim()"
            @click="handlePostDiscussion"
          >
            <el-icon><Promotion /></el-icon> 发送
          </el-button>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Calendar,
  Document,
  View,
  Hide,
  Download,
  StarFilled,
  ChatDotRound,
  ChatLineRound,
  Close,
  Delete,
  Promotion,
  Right,
  Picture,
} from '@element-plus/icons-vue'
import {
  getExcellentQuestions,
  type ExcellentQuestion as LegacyExcellentQuestion,
} from '@/api/modules/excellent-questions'
import {
  getDiscussions,
  postDiscussion,
  deleteDiscussion,
  type DiscussionItem,
  type ReplyItem,
} from '@/api/modules/discussions'
import { parseMarkdown } from '@/utils/markdown'
import { useUserStore } from '@/stores/user'
import { downloadText, prototypeState } from '@/prototype/store'
import type { PrototypeQuestion } from '@/prototype/types'

type ExcellentQuestion = LegacyExcellentQuestion & Partial<PrototypeQuestion>
const thinkingLabels: Record<string, string> = {
  C1: '建模与多重表征',
  C2: '科学推理与定量分析',
  C3: '证据论证与科学解释',
  C4: '实验设计与数据评价',
  C5: '批判质疑与方案创新',
  C6: '迁移整合与真实问题解决',
}
const thinkingText = (tags?: string[]) =>
  tags?.length
    ? tags.map((tag) => `${tag} ${thinkingLabels[tag] || tag}`).join('；')
    : '未设置'
const difficultyLabel = (value?: string) =>
  value
    ? { easy: '基础', medium: '中等', hard: '困难' }[value] || value
    : '未记录'

const userStore = useUserStore()
const currentUserId = computed(() => userStore.user?.id ?? 0)
const currentUserRole = computed(() => userStore.user?.role ?? '')

// ─── 列表 ───
const loading = ref(false)
const questionList = ref<ExcellentQuestion[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchKeyword = ref('')
const sortBy = ref('created_at')
const sortOrder = ref('desc')

// ─── 详情弹窗 ───
const detailVisible = ref(false)
const currentQuestion = ref<ExcellentQuestion | null>(null)
const showAnswer = ref(false)
const showExplanation = ref(false)

const parsedOptions = computed(() => {
  if (!currentQuestion.value?.options) return null
  try {
    const p = JSON.parse(currentQuestion.value.options)
    return typeof p === 'object' && p !== null ? p : null
  } catch {
    return null
  }
})

// ─── 讨论区 ───
const discussionDrawerVisible = ref(false)
const discussionQuestion = ref<ExcellentQuestion | null>(null)
const discussions = ref<DiscussionItem[]>([])
const discussionLoading = ref(false)
const discussionPage = ref(1)
const discussionPageSize = 20
const discussionTotal = ref(0)
const newDiscContent = ref('')
const submitting = ref(false)
const discussionListRef = ref<HTMLElement | null>(null)

// 回复状态
interface ReplyTarget {
  topId: number // 顶层讨论 id（回复框挂在此处）
  parentId: number // 真正回复的 id（可能是顶层或某条回复）
  toUsername: string
  previewText: string // 被回复内容的预览片段
}
const replyTarget = ref<ReplyTarget | null>(null)
const replyContent = ref('')

const hasMoreDiscs = computed(
  () => discussions.value.length < discussionTotal.value,
)

// ─── 加载习题列表 ───
const loadQuestions = async () => {
  loading.value = true
  try {
    const res = await getExcellentQuestions({
      page: currentPage.value,
      page_size: pageSize.value,
      keyword: searchKeyword.value || undefined,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
    })
    questionList.value = res.items
    total.value = res.total
  } catch {
    ElMessage.error('加载优秀习题失败')
  } finally {
    loading.value = false
  }
}
const handleSearch = () => {
  currentPage.value = 1
  loadQuestions()
}

// ─── 详情弹窗 ───
const showDetail = (item: ExcellentQuestion) => {
  currentQuestion.value = item
  showAnswer.value = false
  showExplanation.value = false
  detailVisible.value = true
}
const toggleAnswerVisibility = () => {
  showAnswer.value = !showAnswer.value
}
const toggleExplanationVisibility = () => {
  showExplanation.value = !showExplanation.value
}

// ─── 讨论区：打开 ───
const openDiscussion = async (item: ExcellentQuestion) => {
  discussionQuestion.value = item
  discussions.value = []
  discussionPage.value = 1
  discussionTotal.value = 0
  newDiscContent.value = ''
  replyTarget.value = null
  replyContent.value = ''
  discussionDrawerVisible.value = true
  await loadDiscussions(true)
}

const loadDiscussions = async (reset = false) => {
  if (!discussionQuestion.value) return
  discussionLoading.value = true
  try {
    const res = await getDiscussions({
      question_id: discussionQuestion.value.id,
      page: discussionPage.value,
      page_size: discussionPageSize,
    })
    if (reset) discussions.value = res.items
    else discussions.value.push(...res.items)
    discussionTotal.value = res.total
  } catch {
    ElMessage.error('加载讨论失败')
  } finally {
    discussionLoading.value = false
  }
}

const loadMoreDiscussions = async () => {
  discussionPage.value++
  await loadDiscussions(false)
}

const onDrawerClosed = () => {
  discussions.value = []
  discussionQuestion.value = null
  replyTarget.value = null
}

// ─── 发表顶层讨论 ───
const handlePostDiscussion = async () => {
  if (!newDiscContent.value.trim() || !discussionQuestion.value) return
  if (!currentUserId.value) {
    ElMessage.warning('请先登录')
    return
  }
  if (replyTarget.value) {
    ElMessage.warning('当前处于回复模式，请先取消回复再发新讨论')
    return
  }
  submitting.value = true
  try {
    const item = await postDiscussion({
      question_id: discussionQuestion.value.id,
      user_id: currentUserId.value,
      content: newDiscContent.value.trim(),
    })
    discussions.value.push(item)
    discussionTotal.value++
    newDiscContent.value = ''
    await scrollToBottom()
  } catch {
    ElMessage.error('发表失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

// ─── 回复操作 ───
/** disc = 顶层讨论, reply = 可选的具体回复条目 */
const startReply = (disc: DiscussionItem, reply?: ReplyItem) => {
  const target = reply ?? disc
  const raw = target.content
  replyTarget.value = {
    topId: disc.id,
    parentId: reply ? reply.id : disc.id,
    toUsername: target.username,
    previewText: raw.length > 60 ? raw.slice(0, 60) + '…' : raw,
  }
  replyContent.value = ''
}

const cancelReply = () => {
  replyTarget.value = null
  replyContent.value = ''
}

const handlePostReply = async () => {
  if (
    !replyContent.value.trim() ||
    !replyTarget.value ||
    !discussionQuestion.value
  )
    return
  if (!currentUserId.value) {
    ElMessage.warning('请先登录')
    return
  }
  submitting.value = true
  try {
    const targetSnapshot = { ...replyTarget.value }
    const item = await postDiscussion({
      question_id: discussionQuestion.value.id,
      user_id: currentUserId.value,
      content: replyContent.value.trim(),
      parent_id: targetSnapshot.parentId,
    })
    // 把回复插入对应的顶层讨论 replies 数组（兼容 replies 字段缺失场景）
    const topDisc = discussions.value.find((d) => d.id === targetSnapshot.topId)
    if (topDisc) {
      if (!Array.isArray(topDisc.replies)) topDisc.replies = []
      topDisc.replies.push({
        id: item.id,
        question_id: item.question_id,
        parent_id: targetSnapshot.topId,
        user_id: item.user_id,
        username: item.username,
        role: item.role,
        reply_to_username: item.reply_to_username || targetSnapshot.toUsername,
        content: item.content,
        created_at: item.created_at,
      })
    } else {
      // 极少数情况下本地找不到顶层节点，回退为重新拉取，避免“成功却报错”
      await loadDiscussions(true)
    }
    replyTarget.value = null
    replyContent.value = ''
    ElMessage.success('回复发送成功')
  } catch {
    ElMessage.error('回复失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

// ─── 删除 ───
const handleDeleteDiscussion = async (
  discId: number,
  isReply: boolean,
  topId?: number,
) => {
  try {
    await ElMessageBox.confirm('确定要删除这条讨论吗？', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteDiscussion({
      discussion_id: discId,
      user_id: currentUserId.value,
    })
    if (isReply && topId !== undefined) {
      const top = discussions.value.find((d) => d.id === topId)
      if (top) top.replies = top.replies.filter((r) => r.id !== discId)
    } else {
      discussions.value = discussions.value.filter((d) => d.id !== discId)
      discussionTotal.value = Math.max(0, discussionTotal.value - 1)
    }
    ElMessage.success('已删除')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const canDelete = (item: DiscussionItem | ReplyItem) => {
  if (item.user_id === currentUserId.value) return true
  return (
    currentUserRole.value === 'TEACHER' || currentUserRole.value === 'ADMIN'
  )
}

const scrollToBottom = async () => {
  await nextTick()
  if (discussionListRef.value)
    discussionListRef.value.scrollTop = discussionListRef.value.scrollHeight
}

// ─── 工具函数 ───
const getRoleClass = (role: string) => {
  if (role === 'TEACHER') return 'avatar-teacher'
  if (role === 'ADMIN') return 'avatar-admin'
  return 'avatar-student'
}
const roleLabel = (role: string) => {
  if (role === 'TEACHER') return '教师'
  if (role === 'ADMIN') return '管理员'
  return '学生'
}

const handleDownload = (item: ExcellentQuestion) => {
  if (!item) return
  try {
    const current = prototypeState.questions.find((q) => q.id === item.id)
    const confirmation = current?.confirmations.find(
      (record) => record.version === current.version,
    )
    if (
      !current ||
      current.teacher_status !== 'confirmed' ||
      (current.rating || 0) < 4 ||
      !confirmation
    )
      throw new Error('当前题目已不属于优秀定稿，请刷新列表后重试')
    if (item.version !== undefined && item.version !== current.version)
      throw new Error('题目版本已更新，请重新打开详情后导出')
    let content = `习题：${current.title}\n${'='.repeat(60)}\n\n`
    content += `【知识点】${current.knowledge_point}\n【题型】${getTypeLabel(current.question_type)}\n【认知目标】${getBloomLevelText(current.bloom_level)}\n`
    content += `【目标难度】${difficultyLabel(current.difficulty)}\n【高阶思维能力】${thinkingText(current.thinking_tags)}\n`
    content += `【年级】${current.grade}\n【教师评分】${current.rating || 0} 分\n【创建时间】${formatDate(current.created_at)}\n`
    content += `【教师处理状态】教师已确认\n【确认版本】v${current.version}\n【确认人】${confirmation.teacher_name}\n【确认时间】${formatDate(confirmation.confirmed_at)}\n【配图要求】${current.require_illustration ? '需要配图' : '无需配图'}\n\n`
    content += `${'─'.repeat(60)}\n【习题内容】\n${current.content}\n\n`
    if (current.options) {
      try {
        const opts = JSON.parse(current.options)
        if (typeof opts === 'object' && opts !== null) {
          content += `${'─'.repeat(60)}\n【选项】\n`
          for (const [k, v] of Object.entries(opts)) content += `${k}. ${v}\n`
          content += '\n'
        }
      } catch {
        content += `${'─'.repeat(60)}\n【选项】\n${current.options}\n\n`
      }
    }
    if (current.illustration_url) {
      content += `${'─'.repeat(60)}\n【配图引用】\n${getFullImageUrl(current.illustration_url)}\n\n`
    }
    content += `${'═'.repeat(60)}\n【答案】\n${current.answer}\n\n`
    if (current.explanation)
      content += `${'═'.repeat(60)}\n【解析】\n${current.explanation}\n\n`
    content += `${'─'.repeat(60)}\n【引用来源】\n`
    content += current.evidence.length
      ? current.evidence
          .map(
            (evidence) =>
              `${evidence.source}\n片段：${evidence.fragment_id} | 索引版本：${evidence.index_version}\n${evidence.content}`,
          )
          .join('\n\n')
      : current.kb_reason || '未使用知识库增强'
    downloadText(
      content,
      `${current.title.replace(/[<>:"/\\|?*]/g, '_')}-v${current.version}.txt`,
    )
    ElMessage.success('下载成功')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '下载失败')
  }
}

const getFullImageUrl = (url: string | null | undefined) => {
  if (!url) return ''
  if (/^(https?:|data:image\/|blob:)/i.test(url)) return url
  return new URL(url, window.location.origin + '/').href
}
const getTypeLabel = (type: string) =>
  ({
    single_choice: '单选题',
    multiple_choice: '多选题',
    fill_blank: '填空题',
    short_answer: '简答题',
  })[type.toLowerCase()] || type
const getTypeColor = (type: string) =>
  ({
    single_choice: 'primary',
    multiple_choice: 'success',
    fill_blank: 'warning',
    short_answer: 'info',
  })[type.toLowerCase()] || 'info'
const getBloomLevelType = (bloom: string) =>
  ({
    remember: 'info',
    understand: 'success',
    apply: 'warning',
    analyze: 'danger',
  })[bloom.toLowerCase()] || 'info'
const getBloomLevelText = (bloom: string) =>
  ({ remember: '记忆', understand: '理解', apply: '应用', analyze: '分析' })[
    bloom.toLowerCase()
  ] || bloom
const formatDate = (dateStr: string) =>
  new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })

onMounted(() => {
  loadQuestions()
})
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

/* ─────────────── 讨论区抽屉 ─────────────── */
:deep(.discussion-drawer .el-drawer__body) {
  padding: 0;
  overflow: hidden;
}
.drawer-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f7f8fa;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px 16px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
}
.drawer-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-icon {
  font-size: 24px;
  color: var(--color-primary);
  background: rgba(64, 158, 255, 0.08);
  border-radius: 10px;
  padding: 8px;
}
.drawer-title {
  font-size: 17px;
  font-weight: 700;
  color: #303133;
  line-height: 1.3;
}
.drawer-subtitle {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
  max-width: 330px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 列表滚动区 */
.discussion-list-wrap {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
}
.disc-loading {
  padding: 20px 0;
}
.discussion-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── 顶层讨论 ── */
.disc-thread {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.disc-item {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  position: relative;
  transition: box-shadow 0.2s;
  overflow: hidden;
}
.disc-item:hover {
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
}

/* 顶层讨论卡片 */
.disc-top {
  border: 1px solid #ebeef5;
}
.disc-top.disc-mine {
  border-color: #d0e8ff;
}

/* 顶层类型标记行 */
.disc-type-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  background: linear-gradient(90deg, #f0f7ff, #f7fbff);
  border-bottom: 1px solid #e8f1ff;
  font-size: 11px;
  font-weight: 600;
  color: #409eff;
  border-radius: 12px 12px 0 0;
}
.disc-top.disc-mine .disc-type-badge {
  background: linear-gradient(90deg, #e0f0ff, #edf6ff);
}

/* 主内容行（头像 + body） */
.disc-main-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px 10px;
}

.disc-item.disc-mine .disc-main-row {
  /* 自己发的高亮背景 */
  background: linear-gradient(135deg, #f5f9ff, #edf5ff);
}

/* ── 回复区 ── */
.replies-wrap {
  margin-left: 28px;
  margin-top: 6px;
  position: relative;
  display: flex;
  gap: 0;
}

/* 左侧竖线 */
.replies-thread-line {
  width: 2px;
  flex-shrink: 0;
  background: linear-gradient(180deg, #93c6fd, #c8e2ff);
  border-radius: 2px;
  margin-right: 10px;
}

.replies-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* 回复卡片 */
.reply-item {
  border: 1px solid #e8f1ff;
  border-left: 3px solid #409eff;
  background: #f8fbff;
}
.reply-item.disc-mine {
  background: linear-gradient(135deg, #eef6ff, #e4f0ff);
  border-color: #b8d9ff;
  border-left-color: #409eff;
}

/* 回复头部标记行 */
.reply-header-bar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px 4px;
  background: linear-gradient(90deg, #eef5ff, #f5f9ff);
  border-bottom: 1px solid #deeeff;
  font-size: 11px;
  color: #8cb4e8;
  border-radius: 9px 9px 0 0;
}
.reply-arrow-icon {
  font-size: 11px;
  color: #409eff;
}
.reply-label {
  color: #8cb4e8;
}
.reply-to-name {
  color: #409eff;
  font-weight: 700;
}

/* 头像 */
.disc-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
  user-select: none;
}
.disc-avatar-sm {
  width: 26px;
  height: 26px;
  font-size: 11px;
}
.avatar-teacher {
  background: linear-gradient(135deg, #e6a23c, #f5c077);
}
.avatar-admin {
  background: linear-gradient(135deg, #f56c6c, #fa9898);
}
.avatar-student {
  background: linear-gradient(135deg, #409eff, #79bbff);
}

.disc-body {
  flex: 1;
  min-width: 0;
}
.disc-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 5px;
  flex-wrap: wrap;
}
.disc-username {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.role-tag {
  transform: scale(0.88);
  transform-origin: left;
}
.disc-time {
  font-size: 12px;
  color: #c0c4cc;
  margin-left: auto;
}
.disc-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.7;
  word-break: break-word;
  white-space: pre-wrap;
}

/* 回复 / 删除按钮 */
.disc-actions {
  margin-top: 4px;
}
.reply-btn {
  color: #b0b8c9 !important;
  font-size: 12px !important;
  padding: 0 !important;
}
.reply-btn:hover {
  color: var(--color-primary) !important;
}
.disc-delete-btn {
  position: absolute;
  top: 28px;
  right: 10px;
  opacity: 0;
  transition: opacity 0.2s;
  padding: 2px 4px !important;
}
.disc-item:hover .disc-delete-btn {
  opacity: 1;
}

/* ── 内联回复框 ── */
.inline-reply-box {
  margin-left: 40px;
  margin-top: 6px;
  background: #fff;
  border: 1px solid #93c6fd;
  border-left: 3px solid #409eff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

/* 引用块 */
.reply-quote {
  padding: 8px 14px;
  background: linear-gradient(90deg, #eef5ff, #f5f9ff);
  border-bottom: 1px dashed #c2deff;
}
.reply-quote-from {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #409eff;
  font-weight: 600;
  margin-bottom: 4px;
}
.reply-quote-name {
  color: #2878ff;
}
.reply-quote-text {
  font-size: 12px;
  color: #8a9ab5;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 输入区 */
.inline-reply-input-row {
  padding: 10px 12px 6px;
}
.inline-reply-input-row .disc-textarea {
  width: 100%;
}
.inline-reply-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  padding: 4px 12px 10px;
}
.inline-send-btn {
  border-radius: 16px;
}

/* 加载更多 */
.load-more {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

/* 底部输入 */
.disc-input-area {
  padding: 12px 16px 16px;
  background: #fff;
  border-top: 1px solid #ebeef5;
  flex-shrink: 0;
}
.disc-input-area.is-replying-mode {
  background: linear-gradient(180deg, #fffdf5, #fff);
  border-top-color: #f0d79d;
}
.disc-input-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}
.disc-input-label {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 0;
}
.reply-mode-tip {
  margin-bottom: 8px;
  font-size: 12px;
  color: #a57b1d;
  background: #fff5da;
  border: 1px solid #f3ddb0;
  border-radius: 8px;
  padding: 6px 10px;
}
.disc-input-wrap {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.disc-textarea :deep(.el-textarea__inner) {
  border-radius: 10px;
  font-size: 14px;
  resize: none;
  background: #f7f8fa;
  border-color: #e4e7ed;
}
.disc-textarea :deep(.el-textarea__inner:focus) {
  background: #fff;
  border-color: var(--color-primary);
}
.disc-submit-btn {
  align-self: flex-end;
  border-radius: 20px;
  padding: 8px 22px;
}
</style>
