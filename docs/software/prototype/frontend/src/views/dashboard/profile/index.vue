<template>
  <div class="profile-page">
    <el-row :gutter="20">
      <!-- 左侧用户信息卡片 -->
      <el-col :xs="24" :md="8">
        <el-card class="user-info-card">
          <div class="user-avatar-section">
            <el-avatar
              :size="100"
              :src="userProfile?.avatar_url || defaultAvatar"
            />
            <el-button
              type="primary"
              size="small"
              class="upload-btn"
              @click="showUploadDialog = true"
            >
              <el-icon><Upload /></el-icon>
              更换头像
            </el-button>
          </div>
          <div class="user-basic-info">
            <h3 class="username">{{ userProfile?.username }}</h3>
            <el-tag size="small" :type="userRoleType">{{
              userRoleText
            }}</el-tag>
          </div>
          <div class="user-stats">
            <div class="stat-item">
              <div class="stat-value">
                {{ profileStats?.total_questions || 0 }}
              </div>
              <div class="stat-label">生成习题</div>
            </div>
          </div>
          <el-divider />
          <div class="user-meta">
            <div class="meta-item">
              <el-icon><Clock /></el-icon>
              <span>注册时间：{{ formatDate(userProfile?.created_at) }}</span>
            </div>
          </div>
        </el-card>

        <!-- 菜单导航 -->
        <el-card class="menu-card" style="margin-top: 20px">
          <el-menu :default-active="activeTab" @select="handleMenuSelect">
            <el-menu-item index="profile">
              <el-icon><User /></el-icon>
              <span>基本信息</span>
            </el-menu-item>
            <el-menu-item index="security">
              <el-icon><Lock /></el-icon>
              <span>账户安全</span>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <!-- 右侧内容区域 -->
      <el-col :xs="24" :md="16">
        <!-- 基本信息 -->
        <el-card v-show="activeTab === 'profile'" class="content-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">基本信息</span>
              <el-button
                type="primary"
                :disabled="loadingProfile"
                @click="editProfile = !editProfile"
              >
                {{ editProfile ? '取消编辑' : '编辑资料' }}
              </el-button>
            </div>
          </template>
          <el-form :model="profileForm" label-width="100px">
            <el-form-item label="用户名">
              <el-input :model-value="userProfile?.username" disabled />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input
                v-if="editProfile"
                v-model="profileForm.email"
                placeholder="请输入邮箱"
              />
              <span v-else>{{ userProfile?.email || '未设置' }}</span>
            </el-form-item>
            <el-form-item label="角色">
              <el-tag :type="userRoleType">{{ userRoleText }}</el-tag>
            </el-form-item>
            <el-form-item v-if="editProfile">
              <el-button type="primary" @click="handleUpdateProfile"
                >保存修改</el-button
              >
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 账户安全 -->
        <el-card v-show="activeTab === 'security'" class="content-card">
          <template #header>
            <span class="card-title">账户安全</span>
          </template>
          <el-form
            :model="passwordForm"
            :rules="passwordRules"
            ref="passwordFormRef"
            label-width="120px"
          >
            <el-form-item label="原密码" prop="old_password">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                placeholder="请输入原密码"
                show-password
              />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="请输入新密码"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleChangePassword"
                >修改密码</el-button
              >
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 头像上传弹窗 -->
    <el-dialog v-model="showUploadDialog" title="更换头像" width="400px">
      <el-upload
        class="avatar-uploader"
        :auto-upload="true"
        :show-file-list="false"
        :http-request="handleAvatarUpload"
        accept="image/*"
      >
        <img v-if="tempAvatarUrl" :src="tempAvatarUrl" class="avatar-preview" />
        <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
      </el-upload>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveAvatar">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Upload, Clock, Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import {
  getProfileInfo,
  updateProfileInfo,
  changePassword,
  getProfileStats,
  type UserProfile,
  type ProfileStats,
} from '@/api/modules/profile'

const userStore = useUserStore()
const activeTab = ref('profile')
const editProfile = ref(false)
const showUploadDialog = ref(false)
const tempAvatarUrl = ref('')

const defaultAvatar = '/avatar.svg'

const userProfile = ref<UserProfile | null>(null)
const loadingProfile = ref(true)
const profileStats = ref<ProfileStats | null>(null)

const profileForm = ref({
  email: '',
})

const passwordForm = ref({
  old_password: '',
  new_password: '',
})

const passwordFormRef = ref<FormInstance>()

const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' },
    {
      min: 6,
      max: 50,
      message: '密码长度应在 6-50 个字符之间',
      trigger: 'blur',
    },
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    {
      min: 6,
      max: 50,
      message: '密码长度应在 6-50 个字符之间',
      trigger: 'blur',
    },
  ],
}

const userRoleText = computed(() => {
  const roleMap: Record<string, string> = {
    TEACHER: '教师',
    STUDENT: '学生',
    ADMIN: '管理员',
  }
  return roleMap[userProfile.value?.role || 'TEACHER']
})

const userRoleType = computed(() => {
  const typeMap: Record<string, any> = {
    TEACHER: 'primary',
    STUDENT: 'success',
    ADMIN: 'danger',
  }
  return typeMap[userProfile.value?.role || 'TEACHER']
})

const loadProfile = async () => {
  if (!userStore.user?.id) return
  loadingProfile.value = true
  try {
    const res = await getProfileInfo({ user_id: userStore.user.id })
    userProfile.value = res
    profileForm.value.email = res.email || ''
  } catch (error) {
    ElMessage.error('加载用户信息失败')
  } finally {
    loadingProfile.value = false
  }
}

const loadProfileStats = async () => {
  if (!userStore.user?.id) return

  try {
    const res = await getProfileStats({ user_id: userStore.user.id })
    profileStats.value = res
  } catch (error) {
    ElMessage.error('加载统计信息失败')
  }
}

const handleUpdateProfile = async () => {
  if (!userStore.user?.id) return
  if (
    profileForm.value.email &&
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profileForm.value.email)
  ) {
    ElMessage.error('请输入有效的邮箱地址')
    return
  }

  try {
    await updateProfileInfo(
      { email: profileForm.value.email },
      { user_id: userStore.user.id },
    )
    ElMessage.success('用户信息更新成功')
    editProfile.value = false
    loadProfile()
  } catch (error) {
    ElMessage.error('更新用户信息失败')
  }
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    if (!userStore.user?.id) return

    try {
      await changePassword(passwordForm.value, { user_id: userStore.user.id })
      ElMessage.success('密码修改成功')
      passwordForm.value = { old_password: '', new_password: '' }
      passwordFormRef.value?.resetFields()
    } catch (error: any) {
      const errorMsg =
        error?.response?.data?.detail || '密码修改失败，请检查原密码是否正确'
      ElMessage.error(errorMsg)
    }
  })
}

const handleAvatarUpload = (options: any) => {
  const file = options.file
  const reader = new FileReader()
  reader.onload = (e) => {
    tempAvatarUrl.value = e.target?.result as string
  }
  reader.readAsDataURL(file)
}

const handleSaveAvatar = async () => {
  if (!tempAvatarUrl.value) {
    ElMessage.warning('请选择头像图片')
    return
  }

  try {
    await updateProfileInfo(
      { avatar_url: tempAvatarUrl.value },
      { user_id: userStore.user!.id },
    )
    await loadProfile()
  } catch (error: any) {
    ElMessage.error(error.message)
    return
  }

  showUploadDialog.value = false
  tempAvatarUrl.value = ''
  ElMessage.success('头像更新成功')
}

const handleMenuSelect = (index: string) => {
  activeTab.value = index
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  loadProfile()
  loadProfileStats()
})
</script>

<style scoped>
.profile-page {
  padding: 20px;
  background-color: #f5f7fa;
  height: 100%;
  overflow-y: auto;
}

.user-info-card {
  text-align: center;
}

.user-avatar-section {
  margin-bottom: 20px;
}

.upload-btn {
  margin-top: 10px;
}

.user-basic-info .username {
  margin: 10px 0;
  font-size: 20px;
  color: #303133;
}

.user-stats {
  display: flex;
  justify-content: space-around;
  margin: 20px 0;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.user-meta {
  text-align: left;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 13px;
  color: #606266;
}

.menu-card {
  padding: 0;
}

.menu-card .el-menu {
  border-right: none;
}

.content-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.avatar-uploader {
  display: flex;
  justify-content: center;
  margin: 20px 0;
}

.avatar-uploader-icon {
  width: 150px;
  height: 150px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #8c939d;
}

.avatar-preview {
  width: 150px;
  height: 150px;
  object-fit: cover;
  border-radius: 6px;
}
</style>
