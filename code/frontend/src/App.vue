<template>
  <router-view />
</template>

<style>
#app {
  width: 100%;
  height: 100vh;
  margin: 0;
  padding: 0;
  overflow: hidden;
}
#app > .dashboard-container,
#app > .admin-container,
#app > .login-container {
  height: 100dvh;
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
