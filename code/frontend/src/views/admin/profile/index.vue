<template>
  <div class="profile-container">
    <el-card class="header-card">
      <div class="title-section">
        <h2>个人中心</h2>
        <span class="subtitle">查看当前管理员账号的基础信息</span>
      </div>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>账号信息</span>
        </div>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户ID">
          {{ userStore.user?.id }}
        </el-descriptions-item>
        <el-descriptions-item label="用户名">
          {{ userStore.user?.username }}
        </el-descriptions-item>
        <el-descriptions-item label="邮箱">
          {{ userStore.user?.email || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag type="danger">管理员</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
</script>

<style scoped>
.profile-container {
  max-width: 860px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.title-section h2 {
  margin: 0 0 6px;
  font-size: 24px;
}

.subtitle {
  color: var(--color-text-secondary);
}

.card-header {
  font-weight: 600;
}
</style>
