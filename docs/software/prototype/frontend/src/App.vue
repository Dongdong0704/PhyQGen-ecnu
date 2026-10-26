<template>
  <div class="prototype-banner">
    PhyQGen 交互原型 · 本地预置题例演示，未连接数据库或 AI 服务
  </div>
  <div v-if="storageError.message" class="storage-alert" role="alert">
    {{ storageError.message }}
  </div>
  <router-view />
</template>

<script setup lang="ts">
import { storageError } from '@/prototype/store'
</script>

<style>
#app {
  width: 100%;
  height: 100vh;
  margin: 0;
  padding: 0;
  overflow: hidden;
}
.prototype-banner {
  height: 29px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #edf4ff;
  color: #45658d;
  font-size: 12px;
  border-bottom: 1px solid #dce7f6;
  padding: 0 8px;
}
.storage-alert {
  position: fixed;
  top: 36px;
  left: 20%;
  right: 20%;
  padding: 12px;
  background: #fff0ef;
  border: 1px solid #ffaaa1;
  z-index: 9999;
}
#app > .dashboard-container,
#app > .admin-container,
#app > .login-container {
  height: calc(100dvh - 29px);
}
.el-dialog {
  max-width: calc(100vw - 24px);
}
.header-title {
  margin-left: 16px;
  color: #4f5d7a;
  font-size: 14px;
}
.app-main {
  display: block !important;
}
.app-main > * {
  flex: none !important;
}
@media (max-width: 700px) {
  .prototype-banner {
    font-size: 10px;
  }
  .el-aside {
    width: 72px !important;
  }
  .el-aside .logo h2,
  .el-aside .el-menu-item span {
    display: none;
  }
  .el-aside .el-menu-item {
    padding-left: 12px !important;
  }
  .el-main {
    padding: 12px !important;
  }
  .el-dialog {
    width: calc(100vw - 24px) !important;
  }
}
</style>
