<template>
  <el-container class="admin-container">
    <el-aside :width="sidebarCollapsed ? '72px' : '240px'" class="app-aside">
      <div class="logo app-logo">
        <div class="logo-icon-wrap" v-if="!sidebarCollapsed">
          <el-icon><Setting /></el-icon>
        </div>
        <h2 v-if="!sidebarCollapsed">管理后台</h2>
        <el-icon v-else :size="28" class="collapsed-logo"><Setting /></el-icon>
      </div>
      <el-menu
        class="app-menu"
        :default-active="activeMenu"
        :collapse="sidebarCollapsed"
        router
      >
        <el-menu-item index="/admin/users" aria-label="用户管理">
          <el-icon><UserFilled /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/settings" aria-label="系统维护">
          <el-icon><Key /></el-icon>
          <template #title>系统维护</template>
        </el-menu-item>
        <el-menu-item index="/admin/profile" aria-label="个人中心">
          <el-icon><Setting /></el-icon>
          <template #title>个人中心</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <el-icon class="toggle-btn" @click="toggleSidebar">
            <Fold v-if="!sidebarCollapsed" />
            <Expand v-else />
          </el-icon>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              {{ userStore.user?.username || '用户' }}
              <el-tag type="danger" size="small" class="role-tag"
                >管理员</el-tag
              >
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Setting,
  UserFilled,
  Key,
  User,
  Fold,
  Expand,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()

const sidebarCollapsed = computed(() => appStore.sidebarCollapsed)
const activeMenu = computed(() => route.path)

function toggleSidebar() {
  appStore.toggleSidebar()
}

async function handleCommand(command: string) {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
      userStore.logout()
      ElMessage.success('退出成功')
      router.push('/login')
    } catch {}
  }
}
</script>

<style scoped>
.admin-container {
  width: 100%;
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(180deg, #f7fbff 0%, #f3f6fb 100%);
}

.el-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.el-aside {
  overflow-x: hidden;
  overflow-y: auto;
  background: linear-gradient(180deg, #f7fbff 0%, #f3f6fb 100%);
  transition: width 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
  border-right: 1px solid rgba(0, 0, 0, 0.04);
  z-index: 10;
}

.logo {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-primary);
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 1px;
  background: transparent;
  margin-bottom: 10px;
  position: relative;
}

.logo::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 20px;
  right: 20px;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(0, 0, 0, 0.04),
    transparent
  );
}

.logo-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--color-primary), #66b1ff);
  color: #ffffff;
  margin-right: 12px;
  box-shadow: 0 4px 10px rgba(64, 158, 255, 0.3);
}

.collapsed-logo {
  color: var(--color-primary);
}

.el-header {
  background-color: rgba(255, 255, 255, 0.85);
  border-bottom: none;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  flex-shrink: 0;
  z-index: 5;
}

.toggle-btn {
  font-size: 21px;
  cursor: pointer;
  color: #6c7a96;
  transition:
    color 0.2s ease,
    transform 0.2s ease;
}

.toggle-btn:hover {
  color: var(--color-primary);
  transform: scale(1.06);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--color-text-regular);
}

.role-tag {
  margin-left: 2px;
  border-radius: 999px;
}

.user-info:hover {
  color: var(--color-primary);
}

.el-main {
  background-color: transparent;
  padding: 24px;
  overflow-x: hidden;
  overflow-y: auto;
  flex: 1;
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
}

.el-main :deep(> *) {
  overflow-x: hidden;
  flex: 1;
}

.app-menu {
  border-right: none;
  background-color: transparent;
  padding: 0 12px;
}

.app-menu :deep(.el-menu-item) {
  margin: 8px 0;
  border-radius: 12px;
  color: var(--color-text-regular);
  height: 50px;
  line-height: 50px;
  transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
  position: relative;
}

.app-menu :deep(.el-menu-item:hover) {
  background-color: rgba(64, 158, 255, 0.08);
  color: var(--color-primary);
}

.app-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(
    90deg,
    rgba(64, 158, 255, 0.12) 0%,
    rgba(64, 158, 255, 0.02) 100%
  );
  color: var(--color-primary);
  font-weight: 600;
}

.app-menu :deep(.el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  height: 24px;
  width: 4px;
  background: var(--color-primary);
  border-radius: 0 4px 4px 0;
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.4);
  opacity: 1;
}
</style>
