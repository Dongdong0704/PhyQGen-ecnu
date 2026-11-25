<template>
  <div v-loading="loading" class="settings-container">
    <el-card>
      <div class="card-heading">
        <h2>系统维护</h2>
        <el-button :icon="Refresh" :disabled="loading" @click="load">刷新</el-button>
      </div>
      <p>教师可在个人中心配置模型 API。</p>
    </el-card>
    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />
    <el-row v-if="status" :gutter="20">
      <el-col :xs="24" :lg="14">
        <el-card>
          <template #header>
            <div class="card-heading">
              <span><el-icon><Collection /></el-icon> 知识库索引</span>
              <el-tag :type="status.kb_enabled ? 'success' : 'info'">{{ status.kb_status }}</el-tag>
            </div>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="当前索引版本">{{ status.kb_version }}</el-descriptions-item>
            <el-descriptions-item label="资料片段">{{ status.kb_fragments }} 条</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="10">
        <el-card>
          <template #header><el-icon><Operation /></el-icon> 任务执行</template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="逐题并发上限">{{ status.concurrency }} 道</el-descriptions-item>
            <el-descriptions-item label="单批题量上限">{{ status.batch_size }} 道</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
    <el-card v-if="status">
      <template #header><el-icon><Clock /></el-icon> 维护操作记录</template>
      <el-table :data="visibleAudits" empty-text="暂无账号维护记录" stripe>
        <el-table-column label="操作内容" prop="action" min-width="220" />
        <el-table-column label="操作者" prop="actor" min-width="120" />
        <el-table-column label="时间" min-width="180">
          <template #default="{ row }">{{ formatTime(row.time) }}</template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="status.audits.length > 10"
        v-model:current-page="page"
        :total="status.audits.length"
        :page-size="10"
        layout="prev, pager, next"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Clock, Collection, Operation, Refresh } from '@element-plus/icons-vue'
import { getSystemStatus, type SystemStatus } from '@/api/modules/admin'

const status = ref<SystemStatus>()
const loading = ref(false)
const error = ref('')
const page = ref(1)
const visibleAudits = computed(() => status.value?.audits.slice((page.value - 1) * 10, page.value * 10) ?? [])
const formatTime = (value: string) => new Date(value).toLocaleString('zh-CN', { hour12: false })

async function load() {
  loading.value = true
  error.value = ''
  try {
    status.value = await getSystemStatus()
    page.value = 1
  } catch (cause) {
    error.value = (cause as Error).message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.settings-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.card-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.card-heading h2 {
  margin: 0;
  font-size: 24px;
}
.settings-container p {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
}
.el-row {
  row-gap: 16px;
}
.el-pagination {
  margin-top: 12px;
}
</style>
