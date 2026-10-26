<template>
  <div class="tasks-page">
    <div class="page-heading">
      <div>
        <div class="eyebrow">GENERATION HISTORY</div>
        <h2>生成任务</h2>
        <p>跟踪每一道题的进度，继续审核已保存的草稿。</p>
      </div>
      <el-button
        type="primary"
        :icon="Plus"
        @click="router.push('/question-gen')"
        >新建生成任务</el-button
      >
    </div>
    <div class="summary-strip">
      <div>
        <strong>{{ ownTasks.length }}</strong
        ><span>全部任务</span>
      </div>
      <div>
        <strong>{{ runningCount }}</strong
        ><span>进行中</span>
      </div>
      <div>
        <strong>{{ completedCount }}</strong
        ><span>已有草稿</span>
      </div>
      <div>
        <strong>{{ failedCount }}</strong
        ><span>任务失败</span>
      </div>
    </div>
    <el-alert
      class="demo-note"
      title="原型任务记录保存在当前浏览器，刷新后可继续查看进度与结果。生成过程使用预置题例模拟。"
      type="info"
      :closable="false"
      show-icon
    />
    <el-card class="history-card">
      <template #header
        ><div class="history-heading">
          <h3>任务记录</h3>
          <span>{{ filteredTasks.length }} 个任务</span>
        </div></template
      >
      <div class="toolbar">
        <el-input
          v-model="keyword"
          :prefix-icon="Search"
          placeholder="搜索知识点或任务编号"
          clearable
          aria-label="搜索任务"
        /><el-select v-model="statusFilter" aria-label="任务状态"
          ><el-option label="全部任务" value="all" /><el-option
            label="进行中"
            value="running" /><el-option
            label="已有草稿"
            value="completed" /><el-option label="任务失败" value="failed"
        /></el-select>
      </div>
      <el-table
        v-if="filteredTasks.length"
        :data="pagedTasks"
        row-key="id"
        :row-class-name="rowClassName"
        @row-click="selectTask"
      >
        <el-table-column label="命题要求" min-width="190"
          ><template #default="{ row }"
            ><div class="topic-title">{{ row.params.knowledge_point }}</div>
            <div class="task-time">
              {{ formatTime(row.created_at) }}
            </div></template
          ></el-table-column
        >
        <el-table-column label="题量 / 草稿" width="115"
          ><template #default="{ row }"
            >{{ row.params.count }} 道 / {{ draftCount(row) }} 道</template
          ></el-table-column
        >
        <el-table-column label="执行阶段" min-width="150"
          ><template #default="{ row }"
            ><el-tag
              :type="
                !row.completed
                  ? 'primary'
                  : draftCount(row)
                    ? 'success'
                    : 'danger'
              "
              size="small"
              >{{ row.stage }}</el-tag
            ><el-progress
              v-if="!row.completed"
              class="table-progress"
              :percentage="Math.round(row.progress)"
              :stroke-width="4"
              :show-text="false" /></template
        ></el-table-column>
        <el-table-column label="任务编号" min-width="190"
          ><template #default="{ row }"
            ><span class="task-code">{{ row.id }}</span></template
          ></el-table-column
        >
        <el-table-column label="操作" width="90" fixed="right"
          ><template #default="{ row }"
            ><el-button
              type="primary"
              text
              size="small"
              @click.stop="selectTask(row)"
              >查看详情</el-button
            ></template
          ></el-table-column
        >
      </el-table>
      <el-empty
        v-else
        :description="
          ownTasks.length
            ? '没有找到匹配的任务'
            : '还没有生成任务，从设置一份出题要求开始'
        "
        ><el-button
          v-if="!ownTasks.length"
          type="primary"
          @click="router.push('/question-gen')"
          >开始生成习题</el-button
        ><el-button v-else @click="clearFilters">清除筛选</el-button></el-empty
      >
      <el-pagination
        v-if="filteredTasks.length > pageSize"
        v-model:current-page="page"
        :page-size="pageSize"
        :total="filteredTasks.length"
        layout="prev, pager, next, total"
        class="pagination"
      />
    </el-card>
    <el-alert
      v-if="route.query.task_id && !selectedTask"
      title="未找到该任务，或当前账号无法访问。请选择自己的任务记录。"
      type="warning"
      :closable="false"
      show-icon
      class="missing-task"
    />
    <TaskProgress
      v-if="selectedTask"
      :task="selectedTask"
      :key="selectedTask.id"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Plus, Search } from '@element-plus/icons-vue'
import TaskProgress from '@/components/prototype/TaskProgress.vue'
import { prototypeState, getCurrentUser } from '@/prototype/store'
import type { GenerationTask } from '@/prototype/types'
const route = useRoute()
const router = useRouter()
const keyword = ref('')
const statusFilter = ref('all')
const page = ref(1)
const pageSize = 8
const ownTasks = computed(() =>
  prototypeState.tasks
    .filter((task) => task.user_id === getCurrentUser()?.id)
    .slice()
    .sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at)),
)
const runningCount = computed(
  () => ownTasks.value.filter((task) => !task.completed).length,
)
const completedCount = computed(
  () =>
    ownTasks.value.filter((task) => task.completed && draftCount(task) > 0)
      .length,
)
const failedCount = computed(
  () =>
    ownTasks.value.filter((task) => task.completed && draftCount(task) === 0)
      .length,
)
const filteredTasks = computed(() =>
  ownTasks.value.filter((task) => {
    const matchesKeyword = `${task.params.knowledge_point} ${task.id}`
      .toLowerCase()
      .includes(keyword.value.trim().toLowerCase())
    const matchesStatus =
      statusFilter.value === 'all' ||
      (statusFilter.value === 'running' && !task.completed) ||
      (statusFilter.value === 'completed' &&
        task.completed &&
        draftCount(task) > 0) ||
      (statusFilter.value === 'failed' &&
        task.completed &&
        draftCount(task) === 0)
    return matchesKeyword && matchesStatus
  }),
)
const pagedTasks = computed(() =>
  filteredTasks.value.slice((page.value - 1) * pageSize, page.value * pageSize),
)
const selectedTask = computed(() =>
  route.query.task_id
    ? ownTasks.value.find((task) => task.id === String(route.query.task_id))
    : ownTasks.value[0],
)
watch([keyword, statusFilter], () => {
  page.value = 1
})
function draftCount(task: GenerationTask) {
  return task.items.filter((item) => item.status === 'draft').length
}
function selectTask(task: GenerationTask) {
  router.replace({ path: '/tasks', query: { task_id: task.id } })
}
function rowClassName({ row }: { row: GenerationTask }) {
  return row.id === selectedTask.value?.id ? 'selected-task' : ''
}
function clearFilters() {
  keyword.value = ''
  statusFilter.value = 'all'
}
function formatTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}
</script>

<style scoped>
.tasks-page {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding-bottom: 30px;
}
.page-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
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
.page-heading p {
  color: var(--color-text-secondary);
  line-height: 1.7;
}
.summary-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.summary-strip > div {
  display: flex;
  gap: 10px;
  align-items: baseline;
  background: white;
  border: 1px solid #e5edfa;
  border-radius: 11px;
  padding: 20px;
}
.summary-strip strong {
  font-size: 27px;
  font-weight: 650;
  color: var(--color-primary);
}
.summary-strip span {
  color: var(--color-text-secondary);
  font-size: 13px;
}
.demo-note,
.history-card,
.missing-task {
  margin-bottom: 22px;
}
.history-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.history-heading h3 {
  font-size: 17px;
}
.history-heading span {
  color: var(--color-text-secondary);
  font-size: 12px;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}
.toolbar :deep(.el-input) {
  max-width: 380px;
}
.toolbar :deep(.el-select) {
  width: 150px;
}
.topic-title {
  font-weight: 550;
  color: var(--color-text-primary);
}
.task-time {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 5px;
}
.task-code {
  font-size: 11px;
  color: var(--color-text-secondary);
  overflow-wrap: anywhere;
}
.table-progress {
  margin-top: 8px;
}
.history-card :deep(.el-table__row) {
  cursor: pointer;
}
.history-card :deep(.selected-task) {
  --el-table-tr-bg-color: #eef5ff;
}
.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
@media (max-width: 768px) {
  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .summary-strip {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  .summary-strip > div {
    padding: 15px;
  }
  .toolbar {
    flex-wrap: wrap;
  }
  .toolbar :deep(.el-input) {
    max-width: 100%;
    width: 100%;
  }
}
</style>
