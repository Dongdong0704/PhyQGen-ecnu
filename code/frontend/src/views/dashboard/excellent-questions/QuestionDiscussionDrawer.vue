<template>
  <!-- 讨论区抽屉 -->
  <el-drawer
    v-model="visible"
    direction="rtl"
    size="min(100%, max(640px, 62%))"
    :with-header="false"
    class="discussion-drawer"
    title="优秀习题讨论区"
  >
    <div class="drawer-inner">
      <!-- 抽屉头部 -->
      <div class="drawer-header">
        <div class="drawer-header-left">
          <el-icon class="header-icon"><ChatDotRound /></el-icon>
          <div>
            <div class="drawer-title">讨论区</div>
            <div class="drawer-subtitle" v-if="question">
              {{ question.title }}
            </div>
          </div>
        </div>
        <el-button circle text aria-label="关闭讨论区" @click="visible = false">
          <el-icon :size="18"><Close /></el-icon>
        </el-button>
      </div>

      <!-- 讨论列表 -->
      <div class="discussion-list-wrap" ref="discussionListRef">
        <div v-if="discussionError" class="discussion-load-error" role="alert">
          <span>{{ discussionError }}</span>
          <el-button
            v-if="!unavailable"
            text
            type="primary"
            :disabled="discussionLoading || mutationBusy"
            @click="loadDiscussions"
          >重试</el-button>
        </div>
        <div
          v-if="discussionLoading && !initialLoaded"
          class="disc-loading"
        >
          <el-skeleton :rows="5" animated />
        </div>
        <el-empty
          v-else-if="initialLoaded && !discussionError && discussions.length === 0"
          description="暂无讨论"
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
                      :disabled="actionsLocked"
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
                  :loading="deletingId === disc.id"
                  :disabled="actionsLocked"
                  aria-label="删除讨论"
                  @click="handleDeleteDiscussion(disc.id)"
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
                      >@{{ reply.reply_to_username || disc.username }}</span
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
                          :disabled="actionsLocked"
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
                      :loading="deletingId === reply.id"
                      :disabled="actionsLocked"
                      aria-label="删除回复"
                      @click="handleDeleteDiscussion(reply.id, disc.id)"
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
                  placeholder="输入回复"
                  maxlength="2000"
                  :disabled="actionsLocked"
                  resize="none"
                  class="disc-textarea"
                />
              </div>
              <div class="inline-reply-actions">
                <el-button text size="small" :disabled="mutationBusy" @click="cancelReply"
                  >取消</el-button
                >
                <el-button
                  type="primary"
                  size="small"
                  class="inline-send-btn"
                  :loading="submitting"
                  :disabled="actionsLocked || !replyContent.trim()"
                  @click="handlePostReply"
                >
                  <el-icon><Promotion /></el-icon> 发送回复
                </el-button>
              </div>
            </div>
          </div>

          <!-- 加载更多 -->
          <div v-if="nextAfterId !== null && !discussionError" class="load-more">
            <el-button
              text
              :loading="discussionLoading"
              :disabled="mutationBusy"
              @click="loadDiscussions"
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
            :disabled="actionsLocked || !!replyTarget"
            class="disc-textarea"
          />
          <el-button
            type="primary"
            class="disc-submit-btn"
            :loading="submitting"
            :disabled="actionsLocked || !!replyTarget || !newDiscContent.trim()"
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
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatDotRound,
  ChatLineRound,
  Close,
  Delete,
  Promotion,
  Right,
} from '@element-plus/icons-vue'
import { HttpError } from '@/api/http'
import {
  deleteDiscussion,
  getDiscussions,
  postDiscussion,
  type DiscussionItem,
  type ReplyItem,
} from '@/api/modules/discussions'
import type { ExcellentQuestion } from '@/api/modules/excellent-questions'
import { useUserStore } from '@/stores/user'
import { formatDate } from './presentation'

const props = defineProps<{
  modelValue: boolean
  question: ExcellentQuestion | null
}>()
const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
  (event: 'unavailable'): void
}>()
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})
const userStore = useUserStore()
const currentUserId = computed(() => userStore.user?.id)
const currentUserRole = computed(() => userStore.user?.role)

const discussions = ref<DiscussionItem[]>([])
const discussionLoading = ref(false)
const initialLoaded = ref(false)
const nextAfterId = ref<number | null>(null)
const discussionError = ref('')
const unavailable = ref(false)
const newDiscContent = ref('')
const submitting = ref(false)
const deletingId = ref<number | null>(null)
const discussionListRef = ref<HTMLElement | null>(null)
const mutationBusy = computed(() => submitting.value || deletingId.value !== null)
const actionsLocked = computed(
  () => mutationBusy.value || discussionLoading.value || !initialLoaded.value || unavailable.value,
)

interface ReplyTarget {
  topId: number
  parentId: number
  toUsername: string
  previewText: string
}
const replyTarget = ref<ReplyTarget | null>(null)
const replyContent = ref('')

// Every drawer opening owns its requests, including when the same question is reopened.
let drawerSession = 0
function isCurrent(session: number) {
  return props.modelValue && session === drawerSession
}

watch(
  () => [props.modelValue, props.question?.id] as const,
  ([open, questionId]) => {
    drawerSession++
    resetDiscussionPage()
    discussionLoading.value = false
    unavailable.value = false
    newDiscContent.value = ''
    submitting.value = false
    deletingId.value = null
    cancelReply()
    if (open && questionId !== undefined) void loadDiscussions()
  },
  { immediate: true },
)
onBeforeUnmount(() => { drawerSession++ })

async function loadDiscussions() {
  const question = props.question
  const cursor = nextAfterId.value
  if (!question || !props.modelValue || unavailable.value || discussionLoading.value ||
      mutationBusy.value || (initialLoaded.value && cursor === null)) return

  const session = drawerSession
  discussionLoading.value = true
  discussionError.value = ''
  try {
    const result = await getDiscussions({
      question_id: question.id,
      page_size: 20,
      after_id: cursor ?? undefined,
    })
    if (!isCurrent(session)) return
    const merged = new Map(discussions.value.map((item) => [item.id, item]))
    for (const item of result.items) merged.set(item.id, item)
    discussions.value = [...merged.values()].sort((left, right) => left.id - right.id)
    nextAfterId.value = result.next_after_id
    initialLoaded.value = true
  } catch (error) {
    if (!isCurrent(session)) return
    if (error instanceof HttpError && error.status === 404) {
      markUnavailable(error)
    } else {
      discussionError.value = messageFor(error, '加载讨论失败')
    }
  } finally {
    if (isCurrent(session)) discussionLoading.value = false
  }
}

function resetDiscussionPage() {
  discussions.value = []
  initialLoaded.value = false
  nextAfterId.value = null
  discussionError.value = ''
}

function markUnavailable(error: Error) {
  resetDiscussionPage()
  unavailable.value = true
  discussionError.value = error.message
  newDiscContent.value = ''
  cancelReply()
  emit('unavailable')
}

function startReply(thread: DiscussionItem, reply?: ReplyItem) {
  if (actionsLocked.value) return
  const target = reply ?? thread
  replyTarget.value = {
    topId: thread.id,
    parentId: target.id,
    toUsername: target.username,
    previewText: target.content.length > 60 ? target.content.slice(0, 60) + '…' : target.content,
  }
  replyContent.value = ''
}

function cancelReply() {
  replyTarget.value = null
  replyContent.value = ''
}

async function submitDiscussion(content: string, target?: ReplyTarget) {
  const question = props.question
  if (!question || !content || actionsLocked.value) return
  const session = drawerSession
  let refreshThreads = false
  submitting.value = true
  try {
    const posted = await postDiscussion({
      question_id: question.id,
      content,
      parent_id: target?.parentId,
    })
    if (!isCurrent(session)) return

    if (target) {
      const thread = discussions.value.find((item) => item.id === target.topId)
      if (thread && posted.parent_id !== null) {
        const { replies, ...reply } = posted
        thread.replies.push({ ...reply, parent_id: posted.parent_id })
      }
      cancelReply()
      ElMessage.success('回复已发送')
    } else {
      discussions.value.push(posted)
      newDiscContent.value = ''
      await nextTick()
      if (isCurrent(session) && discussionListRef.value) {
        discussionListRef.value.scrollTop = discussionListRef.value.scrollHeight
      }
    }
  } catch (error) {
    if (!isCurrent(session)) return
    if (!target && error instanceof HttpError && error.status === 404) {
      markUnavailable(error)
    } else {
      ElMessage.error(messageFor(error, target ? '回复发送失败' : '发表讨论失败'))
      if (target && error instanceof HttpError && error.status === 404) {
        cancelReply()
        resetDiscussionPage()
        refreshThreads = true
      }
    }
  } finally {
    if (isCurrent(session)) {
      submitting.value = false
      if (refreshThreads) void loadDiscussions()
    }
  }
}

function handlePostDiscussion() {
  if (!replyTarget.value) void submitDiscussion(newDiscContent.value.trim())
}

function handlePostReply() {
  if (replyTarget.value) void submitDiscussion(replyContent.value.trim(), replyTarget.value)
}

async function handleDeleteDiscussion(id: number, topId?: number) {
  if (actionsLocked.value) return
  const session = drawerSession
  deletingId.value = id
  try {
    try {
      await ElMessageBox.confirm(
        topId === undefined ? '删除讨论会同时删除该讨论下的回复。' : '确定删除这条回复吗？',
        topId === undefined ? '删除讨论' : '删除回复',
        { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
      )
    } catch {
      return
    }
    if (!isCurrent(session)) return
    await deleteDiscussion(id)
    if (!isCurrent(session)) return
    if (topId === undefined) {
      discussions.value = discussions.value.filter((item) => item.id !== id)
    } else {
      const thread = discussions.value.find((item) => item.id === topId)
      if (thread) thread.replies = thread.replies.filter((reply) => reply.id !== id)
    }
    if (replyTarget.value?.topId === id || replyTarget.value?.parentId === id) cancelReply()
    ElMessage.success('已删除')
  } catch (error) {
    if (isCurrent(session)) ElMessage.error(messageFor(error, '删除失败'))
  } finally {
    if (isCurrent(session)) deletingId.value = null
  }
}

function canDelete(item: DiscussionItem | ReplyItem) {
  const id = currentUserId.value
  return id !== undefined && (
    currentUserRole.value === 'ADMIN' || item.user_id === id || props.question?.user_id === id
  )
}

const getRoleClass = (role: string) =>
  ({ TEACHER: 'avatar-teacher', ADMIN: 'avatar-admin' })[role] || 'avatar-student'
const roleLabel = (role: string) =>
  ({ TEACHER: '教师', ADMIN: '管理员', STUDENT: '学生' })[role] || role
const messageFor = (error: unknown, fallback: string) =>
  error instanceof Error ? error.message : fallback
</script>

<style scoped>
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
.discussion-load-error {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  margin-bottom: 12px;
  color: var(--el-color-danger);
  background: var(--el-color-danger-light-9);
  border-radius: 8px;
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
.disc-item:hover .disc-delete-btn,
.disc-delete-btn:focus-visible {
  opacity: 1;
}

@media (hover: none) {
  .disc-delete-btn {
    opacity: 1;
  }
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
