<template>
  <div class="users-container">
    <el-card class="header-card">
      <div class="page-header">
        <div class="title-section">
          <h2>用户管理</h2>
          <span class="subtitle">维护教师与管理员账号、角色及启用状态</span>
        </div>
      </div>
    </el-card>

    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="角色">
          <el-select
            v-model="searchForm.role"
            placeholder="全部角色"
            clearable
            @change="loadUsers"
          >
            <el-option label="教师" value="TEACHER" />
            <el-option label="管理员" value="ADMIN" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon>
            新建用户
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" width="200">
          <template #default="{ row }">
            {{ row.email || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role)">
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" fixed="right" width="280">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)"
              >编辑</el-button
            >
            <el-button
              size="small"
              type="warning"
              @click="openPasswordDialog(row)"
              >修改密码</el-button
            >
            <el-button size="small" type="danger" @click="handleDelete(row)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="createDialogVisible" title="新建用户" width="500px">
      <el-form
        :model="createForm"
        :rules="createRules"
        ref="createFormRef"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="createForm.email"
            placeholder="请输入邮箱（可选）"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="createForm.password"
            type="password"
            placeholder="请输入密码"
          />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="createForm.role" placeholder="请选择角色">
            <el-option label="教师" value="TEACHER" />
            <el-option label="管理员" value="ADMIN" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editDialogVisible" title="编辑用户" width="500px">
      <el-form
        :model="editForm"
        :rules="editRules"
        ref="editFormRef"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="editForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" placeholder="请输入邮箱（可选）" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="editForm.role" placeholder="请选择角色">
            <el-option label="教师" value="TEACHER" />
            <el-option label="管理员" value="ADMIN" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="editForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEdit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="passwordDialogVisible" title="修改密码" width="400px">
      <el-form
        :model="passwordForm"
        :rules="passwordRules"
        ref="passwordFormRef"
        label-width="80px"
      >
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="请输入新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdatePassword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  ElMessage,
  ElMessageBox,
  type FormInstance,
  type FormRules,
} from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getUsers,
  createUser,
  updateUser,
  updateUserPassword,
  deleteUser,
  type User,
} from '@/api/modules/admin'

const loading = ref(false)
const users = ref<User[]>([])

const searchForm = reactive({
  role: '',
})

const createDialogVisible = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({
  username: '',
  email: '',
  password: '',
  role: 'TEACHER',
})
const createRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    {
      min: 3,
      max: 50,
      message: '用户名长度在 3 到 50 个字符',
      trigger: 'blur',
    },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' },
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

const editDialogVisible = ref(false)
const editFormRef = ref<FormInstance>()
const editForm = reactive({
  id: 0,
  username: '',
  email: '',
  role: '',
  is_active: true,
})
const editRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    {
      min: 3,
      max: 50,
      message: '用户名长度在 3 到 50 个字符',
      trigger: 'blur',
    },
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

const passwordDialogVisible = ref(false)
const passwordFormRef = ref<FormInstance>()
const passwordForm = reactive({
  userId: 0,
  new_password: '',
})
const passwordRules: FormRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' },
  ],
}

async function loadUsers() {
  loading.value = true
  try {
    const res = await getUsers(searchForm.role || undefined)
    users.value = res.data.users
  } catch (error: any) {
    ElMessage.error(error.message || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

function getRoleLabel(role: string) {
  const labels: Record<string, string> = {
    STUDENT: '学生',
    TEACHER: '教师',
    ADMIN: '管理员',
  }
  return labels[role] || role
}

function getRoleTagType(role: string) {
  const types: Record<string, any> = {
    STUDENT: 'info',
    TEACHER: 'success',
    ADMIN: 'danger',
  }
  return types[role] || ''
}

function openCreateDialog() {
  createForm.username = ''
  createForm.email = ''
  createForm.password = ''
  createForm.role = 'TEACHER'
  createDialogVisible.value = true
}

async function handleCreate() {
  await createFormRef.value?.validate()
  try {
    const data = {
      ...createForm,
      email: createForm.email || undefined,
    }
    await createUser(data)
    ElMessage.success('创建用户成功')
    createDialogVisible.value = false
    loadUsers()
  } catch (error: any) {
    ElMessage.error(error.message || '创建用户失败')
  }
}

function openEditDialog(user: User) {
  editForm.id = user.id
  editForm.username = user.username
  editForm.email = user.email || ''
  editForm.role = user.role
  editForm.is_active = user.is_active
  editDialogVisible.value = true
}

async function handleEdit() {
  await editFormRef.value?.validate()
  try {
    await updateUser(editForm.id, editForm)
    ElMessage.success('更新用户成功')
    editDialogVisible.value = false
    loadUsers()
  } catch (error: any) {
    ElMessage.error(error.message || '更新用户失败')
  }
}

function openPasswordDialog(user: User) {
  passwordForm.userId = user.id
  passwordForm.new_password = ''
  passwordDialogVisible.value = true
}

async function handleUpdatePassword() {
  await passwordFormRef.value?.validate()
  try {
    await updateUserPassword(passwordForm.userId, {
      new_password: passwordForm.new_password,
    })
    ElMessage.success('修改密码成功')
    passwordDialogVisible.value = false
  } catch (error: any) {
    ElMessage.error(error.message || '修改密码失败')
  }
}

async function handleDelete(user: User) {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    await deleteUser(user.id)
    ElMessage.success('删除用户成功')
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除用户失败')
    }
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.users-container {
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

.search-card,
.table-card {
  flex-shrink: 0;
}
</style>
