<template>
  <div class="overview-page">
    <el-card
      ><div class="welcome">
        <div>
          <el-tag effect="dark">教学数据看板</el-tag>
          <h2>{{ userStore.user?.username || '教师' }}，欢迎回来</h2>
          <p>从教学要求到可用习题，每一步都清晰可见。</p>
        </div>
        <el-button
          type="primary"
          :icon="MagicStick"
          @click="router.push('/question-gen')"
          >开始生成习题</el-button
        >
      </div></el-card
    >
    <div class="stats-grid">
      <el-card
        v-for="stat in stats"
        :key="stat.label"
        class="stat-card"
        @click="router.push(stat.path)"
        ><div class="stat-label">
          {{ stat.label }} <el-icon><ArrowRight /></el-icon>
        </div>
        <div class="stat-number" :style="{ color: stat.color }">
          {{ stat.value }}<small> {{ stat.unit }}</small>
        </div>
        <p>{{ stat.hint }}</p></el-card
      >
    </div>
    <el-card
      ><template #header
        ><div class="card-heading">
          <b>出题工作流</b><span>习题生成后，草稿仍需教师人工审核。</span>
        </div></template
      ><el-steps :active="1" align-center
        ><el-step
          title="配置出题要求"
          description="年级 / 题型 / 认知目标" /><el-step
          title="生成习题草稿"
          description="检索 / 文本 / 配图 / 自动校验" /><el-step
          title="教师审核与修改"
          description="检查物理内容和图文一致性" /><el-step
          title="确认定稿并导出"
          description="定稿版本导出 TXT"
      /></el-steps>
      <div class="workflow-links">
        <el-button @click="router.push('/question-gen')">前往习题生成</el-button
        ><el-button
          type="primary"
          plain
          @click="router.push('/question-bank?status=pending')"
          >处理待审核草稿</el-button
        >
      </div></el-card
    >
    <el-card
      ><template #header
        ><div class="card-heading">
          <b>最近的习题</b
          ><el-button type="primary" text @click="router.push('/question-bank')"
            >查看全部 <el-icon><ArrowRight /></el-icon
          ></el-button></div></template
      ><el-table
        :data="recent"
        @row-click="openQuestion"
        style="cursor: pointer"
        ><el-table-column
          prop="title"
          label="习题"
          min-width="230"
        /><el-table-column label="题型" width="95"
          ><template #default="{ row }">{{
            labels[row.question_type]
          }}</template></el-table-column
        ><el-table-column
          prop="grade"
          label="年级"
          width="75"
        /><el-table-column label="教师处理状态" min-width="160"
          ><template #default="{ row }"
            ><el-tag
              :type="row.teacher_status === 'confirmed' ? 'success' : 'warning'"
              >{{
                row.teacher_status === 'confirmed'
                  ? '教师已确认'
                  : '待教师人工审核'
              }}</el-tag
            ></template
          ></el-table-column
        ><el-table-column label="创建时间" min-width="165"
          ><template #default="{ row }">{{
            new Date(row.created_at).toLocaleString('zh-CN')
          }}</template></el-table-column
        ></el-table
      ></el-card
    >
    <div class="chart-grid">
      <el-card v-for="(chart, i) in chartDefs" :key="chart.title"
        ><template #header
          ><b>{{ chart.title }}</b></template
        >
        <div :ref="(el) => setChartEl(el, i)" class="chart"></div
      ></el-card>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { http } from '@/api/http'
import { useUserStore } from '@/stores/user'
import type { PrototypeQuestion } from '@/prototype/types'

interface OverviewStats {
  total_questions: number
  pending_questions: number
  confirmed_questions: number
  total_tasks: number
  recent_questions: PrototypeQuestion[]
  questions_by_knowledge: Record<string, number>
  questions_by_type: Record<string, number>
  questions_by_bloom: Record<string, number>
  questions_by_grade: Record<string, number>
}

const router = useRouter()
const userStore = useUserStore()
const overview = ref<OverviewStats>()
const request = new AbortController()
const recent = computed(() => overview.value?.recent_questions || [])
const stats = computed(() => [
  {
    label: '我的习题',
    value: overview.value?.total_questions ?? 0,
    unit: '道',
    color: '#4d8ff5',
    hint: '草稿与定稿总数',
    path: '/question-bank',
  },
  {
    label: '待教师人工审核',
    value: overview.value?.pending_questions ?? 0,
    unit: '道',
    color: '#d29335',
    hint: '可直接查看、编辑和确认',
    path: '/question-bank?status=pending',
  },
  {
    label: '教师已确认',
    value: overview.value?.confirmed_questions ?? 0,
    unit: '道',
    color: '#3ba487',
    hint: '当前确认版本可导出',
    path: '/question-bank?status=confirmed',
  },
  {
    label: '生成批次',
    value: overview.value?.total_tasks ?? 0,
    unit: '次',
    color: '#7a79d9',
    hint: '已发起的习题生成批次',
    path: '/question-gen',
  },
])
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
const chartDefs = [
  { title: '知识点分布', field: 'questions_by_knowledge' },
  { title: '题型分布', field: 'questions_by_type' },
  { title: '认知目标分布', field: 'questions_by_bloom' },
  { title: '年级分布', field: 'questions_by_grade' },
] as const
const chartEls: HTMLElement[] = [],
  charts: echarts.ECharts[] = []
function setChartEl(el: unknown, i: number) {
  if (el instanceof HTMLElement) chartEls[i] = el
}
function updateCharts() {
  chartDefs.forEach((def, i) => {
    if (!chartEls[i]) return
    const chart = charts[i] || (charts[i] = echarts.init(chartEls[i]))
    const counts = overview.value?.[def.field] || {}
    const data = Object.entries(counts).map(([key, value]) => ({
      name: labels[key] || key,
      value,
    }))
    chart.setOption({
      color: ['#659df7', '#6fc6ac', '#f2c078', '#a299de'],
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [
        {
          type: 'pie',
          radius: ['42%', '68%'],
          center: ['50%', '44%'],
          data,
          label: { show: true, formatter: '{b}: {c}' },
        },
      ],
    })
  })
}
function openQuestion(q: PrototypeQuestion) {
  router.push(`/question-bank?question_id=${q.id}`)
}
function resize() {
  charts.forEach((c) => c.resize())
}
watch(overview, updateCharts, { flush: 'post' })
onMounted(async () => {
  updateCharts()
  window.addEventListener('resize', resize)
  try {
    overview.value = await http<OverviewStats>('/v1/overview/stats', {
      signal: request.signal,
    })
  } catch (error) {
    if (!request.signal.aborted) {
      ElMessage.error(error instanceof Error ? error.message : '概览数据加载失败')
    }
  }
})
onUnmounted(() => {
  request.abort()
  window.removeEventListener('resize', resize)
  charts.forEach((c) => c.dispose())
})
</script>
<style scoped>
.overview-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex-shrink: 0;
}
.welcome,
.card-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.welcome h2 {
  margin: 14px 0 9px;
  font-size: 26px;
}
.welcome p,
.card-heading > span,
.stat-card p {
  color: #7b87a6;
  font-size: 13px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
}
.stat-card {
  cursor: pointer;
}
.stat-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #64728b;
}
.stat-number {
  font-size: 36px;
  font-weight: 650;
  margin: 12px 0;
}
.stat-number small {
  font-size: 13px;
  font-weight: 400;
}
.workflow-links {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 24px;
}
.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}
.chart {
  height: 280px;
}
.overview-page :deep(.el-step__title) {
  font-size: 14px;
}
.overview-page :deep(.el-step__description) {
  font-size: 12px;
}
@media (max-width: 1100px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 700px) {
  .chart-grid {
    grid-template-columns: 1fr;
  }
  .welcome {
    align-items: flex-start;
    flex-direction: column;
  }
  .welcome h2 {
    font-size: 21px;
  }
  .card-heading {
    flex-wrap: wrap;
  }
  .overview-page :deep(.el-step__description) {
    display: none;
  }
}
</style>
