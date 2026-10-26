<template>
  <div class="login-container">
    <div class="decor-circle decor-circle-left" />
    <div class="decor-circle decor-circle-right" />

    <div class="login-shell">
      <section class="login-hero">
        <div class="hero-logo">
          <el-icon class="hero-logo-icon"><Atom /></el-icon>
          <span>PhyQGen</span>
        </div>
        <h1 class="hero-title">物理习题生成平台</h1>
        <p class="hero-desc">
          面向高中物理教师，串联出题配置、习题草稿、人工审核、确认定稿与导出。
        </p>
        <ul class="hero-features">
          <li>
            <el-icon><BookOpenText /></el-icon>
            覆盖题库管理与一键导出
          </li>
          <li>
            <el-icon><GraduationCap /></el-icon>
            支持知识库增强与物理配图
          </li>
          <li>
            <el-icon><Sparkles /></el-icon>
            生成完成后，由教师审核并确认
          </li>
        </ul>
      </section>

      <section class="login-panel">
        <div class="panel-header">
          <h2>欢迎使用</h2>
          <p>请登录或注册后继续访问系统</p>
          <div class="demo-accounts">
            <el-tag type="warning">交互原型 · 预置数据</el-tag>
            <p>教师：teacher / Teacher123</p>
            <p>管理：admin / Admin123</p>
            <el-button size="small" @click="fillDemoAccount('teacher')"
              >填入教师账号</el-button
            ><el-button size="small" @click="fillDemoAccount('admin')"
              >填入管理员账号</el-button
            >
          </div>
        </div>

        <el-tabs v-model="activeTab" class="login-tabs" stretch>
          <el-tab-pane name="login">
            <template #label>
              <span class="tab-label">
                <el-icon><LogIn /></el-icon>
                登录
              </span>
            </template>
            <el-form
              ref="loginFormRef"
              :model="loginForm"
              :rules="loginRules"
              label-position="top"
            >
              <el-form-item label="用户名" prop="username">
                <el-input
                  v-model="loginForm.username"
                  placeholder="请输入用户名"
                  :prefix-icon="User"
                  clearable
                />
              </el-form-item>
              <el-form-item label="密码" prop="password">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="请输入密码"
                  :prefix-icon="LockKeyhole"
                  show-password
                  clearable
                  @keyup.enter="handleLogin"
                />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  class="submit-btn"
                  :icon="LogIn"
                  :loading="loginLoading"
                  @click="handleLogin"
                >
                  登录
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane name="register">
            <template #label>
              <span class="tab-label">
                <el-icon><UserPlus /></el-icon>
                注册
              </span>
            </template>
            <el-form
              ref="registerFormRef"
              :model="registerForm"
              :rules="registerRules"
              label-position="top"
            >
              <el-form-item label="用户名" prop="username">
                <el-input
                  v-model="registerForm.username"
                  placeholder="请输入用户名（3-50字符）"
                  :prefix-icon="User"
                  clearable
                />
              </el-form-item>
              <el-form-item label="邮箱" prop="email">
                <el-input
                  v-model="registerForm.email"
                  placeholder="请输入邮箱（可选）"
                  :prefix-icon="Mail"
                  clearable
                />
              </el-form-item>
              <el-form-item label="密码" prop="password">
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  placeholder="请输入密码（至少6字符）"
                  :prefix-icon="LockKeyhole"
                  show-password
                  clearable
                />
              </el-form-item>
              <el-form-item label="确认密码" prop="confirmPassword">
                <el-input
                  v-model="registerForm.confirmPassword"
                  type="password"
                  placeholder="请再次输入密码"
                  :prefix-icon="LockKeyhole"
                  show-password
                  clearable
                  @keyup.enter="handleRegister"
                />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  class="submit-btn"
                  :icon="UserPlus"
                  :loading="registerLoading"
                  @click="handleRegister"
                >
                  注册
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>

        <p class="panel-tip">
          <el-icon><Sparkles /></el-icon>
          教师原型 · 本地保存演示数据 · 注册仅创建教师账号
        </p>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { login, register } from '@/api/modules/auth'
import {
  Atom,
  BookOpenText,
  GraduationCap,
  LockKeyhole,
  LogIn,
  Mail,
  Sparkles,
  User,
  UserPlus,
} from '@/components/icons'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('login')
const loginLoading = ref(false)
const registerLoading = ref(false)
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()

const loginForm = reactive({
  username: '',
  password: '',
})

function fillDemoAccount(account: 'teacher' | 'admin') {
  loginForm.username = account
  loginForm.password = account === 'teacher' ? 'Teacher123' : 'Admin123'
}

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: 'TEACHER',
  adminKey: '',
})

const validateConfirmPassword = (_rule: any, value: any, callback: any) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' },
  ],
}

const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50个字符', trigger: 'blur' },
  ],
  email: [{ type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

async function handleLogin() {
  if (!loginFormRef.value) {
    return
  }

  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return

    loginLoading.value = true
    try {
      const res = await login({
        username: loginForm.username,
        password: loginForm.password,
      })

      userStore.setToken(res.data.access_token)
      userStore.setUser({
        id: res.data.user.id,
        username: res.data.user.username,
        email: res.data.user.email || '',
        role: res.data.user.role,
      })

      ElMessage.success('登录成功')
      router.push('/')
    } catch (error: any) {
      ElMessage.error(error.message || '登录失败，请稍后重试')
    } finally {
      loginLoading.value = false
    }
  })
}

async function handleRegister() {
  if (!registerFormRef.value) return

  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return

    registerLoading.value = true
    try {
      const res = await register({
        username: registerForm.username,
        email: registerForm.email || undefined,
        password: registerForm.password,
        role: registerForm.role,
      })

      userStore.setToken(res.data.access_token)
      userStore.setUser({
        id: res.data.user.id,
        username: res.data.user.username,
        email: res.data.user.email || '',
        role: res.data.user.role,
      })

      ElMessage.success('注册成功')
      router.push('/')
    } catch (error: any) {
      ElMessage.error(error.message || '注册失败，请稍后重试')
    } finally {
      registerLoading.value = false
    }
  })
}
</script>

<style scoped>
.demo-accounts {
  margin: 18px 0;
  padding: 14px;
  border: 1px solid #dfe8fb;
  border-radius: 10px;
  background: #f5f8ff;
  font-size: 13px;
}
.demo-accounts p {
  margin: 7px 0;
}
.login-container {
  overflow-y: auto !important;
}
.login-container {
  position: relative;
  overflow: hidden;
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(
    140deg,
    var(--color-primary-light) 0%,
    var(--color-primary) 100%
  );
}

.decor-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.14);
  pointer-events: none;
}

.decor-circle-left {
  width: 320px;
  height: 320px;
  top: -120px;
  left: -90px;
}

.decor-circle-right {
  width: 260px;
  height: 260px;
  right: -70px;
  bottom: -110px;
}

.login-shell {
  width: min(960px, 100%);
  min-height: 620px;
  background: var(--color-bg-white);
  border-radius: 24px;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.18);
  display: grid;
  grid-template-columns: 1fr 1.1fr;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.login-hero {
  padding: 44px 36px;
  background: linear-gradient(
    160deg,
    rgba(64, 158, 255, 0.08) 0%,
    rgba(102, 177, 255, 0.2) 100%
  );
  border-right: 1px solid var(--color-border-extra-light);
  display: flex;
  flex-direction: column;
}

.hero-logo {
  width: fit-content;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-radius: 999px;
  background: var(--color-bg-white);
  color: var(--color-primary);
  font-weight: 600;
  box-shadow: var(--box-shadow-base);
}

.hero-logo-icon {
  font-size: 18px;
}

.hero-title {
  margin: 24px 0 14px;
  font-size: 30px;
  line-height: 1.3;
  color: var(--color-text-primary);
}

.hero-desc {
  margin: 0;
  color: var(--color-text-regular);
  line-height: 1.8;
}

.hero-features {
  margin: auto 0 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hero-features li {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.login-panel {
  padding: 44px 38px 34px;
  display: flex;
  flex-direction: column;
}

.panel-header h2 {
  margin: 0;
  font-size: 28px;
  color: var(--color-text-primary);
}

.panel-header p {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.login-tabs {
  margin-top: 20px;
}

.submit-btn {
  width: 100%;
  height: 42px;
  font-size: 15px;
  border-radius: 10px;
}

.panel-tip {
  margin: 18px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-small);
  display: flex;
  align-items: center;
  gap: 6px;
}

@media (max-width: 900px) {
  .login-shell {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .login-hero {
    padding: 28px 24px 20px;
    border-right: 0;
    border-bottom: 1px solid var(--color-border-extra-light);
  }

  .hero-title {
    font-size: 24px;
  }

  .hero-features {
    margin-top: 18px;
  }

  .login-panel {
    padding: 26px 24px 22px;
  }
}
</style>
