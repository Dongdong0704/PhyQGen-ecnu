<template>
  <el-card v-loading="loading">
    <template #header><strong>模型 API 配置</strong></template>
    <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon />
    <el-button v-if="loadError" class="retry" @click="load">重新加载</el-button>
    <el-tabs v-else-if="!loading" v-model="activeRole">
      <el-tab-pane v-for="role in modelRoles" :key="role.id" :name="role.id" :label="role.label">
        <el-form
          v-if="activeRole === role.id"
          label-position="top"
          :disabled="Boolean(editors[role.id].busy)"
          @submit.prevent="save(role.id)"
        >
          <div class="role-status">
            <el-tag v-if="editors[role.id].settings?.configured" type="success">已保存</el-tag>
            <el-tag v-else type="info">未配置</el-tag>
            <el-tag v-if="hasChanges(editors[role.id])" type="warning">有未保存修改</el-tag>
            <span v-if="editors[role.id].settings?.inherited" class="field-help">
              已从旧配置迁移，可单独修改并保存。
            </span>
            <span v-else-if="role.requiresIllustration" class="field-help">生成带配图的习题时使用。</span>
          </div>
          <el-form-item label="OpenAI 兼容 API 地址" required>
            <el-input
              v-model.trim="editors[role.id].base_url"
              placeholder="https://服务商地址/v1"
              maxlength="500"
              @input="editors[role.id].feedback = undefined"
            />
            <div class="field-help">
              填写服务商的 API 基础地址，例如结尾为 /v1 的地址。也可填写完整的
              <code>{{ role.id === 'illustrator' ? '/images/generations' : '/chat/completions' }}</code>
              接口地址。
            </div>
          </el-form-item>
          <el-form-item label="模型名称" required>
            <el-input
              v-model.trim="editors[role.id].model"
              :placeholder="modelPlaceholder[role.id]"
              maxlength="200"
              @input="editors[role.id].feedback = undefined"
            />
          </el-form-item>
          <el-form-item label="API 密钥">
            <el-input
              v-model="editors[role.id].apiKey"
              type="password"
              show-password
              autocomplete="new-password"
              maxlength="1024"
              :disabled="editors[role.id].clearApiKey"
              :placeholder="editors[role.id].settings?.has_api_key ? '已设置，留空保留' : '按服务要求填写'"
              @input="editors[role.id].feedback = undefined"
            />
            <el-checkbox
              v-if="editors[role.id].settings?.has_api_key"
              v-model="editors[role.id].clearApiKey"
              @change="editors[role.id].feedback = undefined"
            >保存时清除已保存的密钥</el-checkbox>
          </el-form-item>
          <p class="field-help test-help">
            {{ role.id === 'illustrator'
              ? '测试会请求生成一张配图，可能消耗一次模型用量。'
              : role.id === 'vision_reviewer'
                ? '测试会向模型发送一张测试图片，验证接口支持图片输入。'
                : '测试会发送一条简短请求，验证所填模型接口能否响应。' }}
          </p>
          <div class="model-actions">
            <el-button type="primary" native-type="submit" :loading="editors[role.id].busy === 'save'">保存配置</el-button>
            <el-button :loading="editors[role.id].busy === 'test'" @click="test(role.id)">测试连接</el-button>
            <el-button
              v-if="editors[role.id].settings?.configured"
              link
              type="danger"
              :loading="editors[role.id].busy === 'remove'"
              @click="remove(role.id, role.label)"
            >清除配置</el-button>
          </div>
          <el-alert
            v-if="editors[role.id].feedback"
            class="model-feedback"
            :type="editors[role.id].feedback?.type"
            :title="editors[role.id].feedback?.message"
            :closable="false"
            show-icon
          />
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import {
  deleteModelSettings,
  getModelSettings,
  modelRoles,
  saveModelSettings,
  testModelSettings,
  type AgentModelSettings,
  type ModelRole,
  type ModelSettings,
  type ModelSettingsUpdate,
} from '@/api/modules/model-settings'

type Action = 'save' | 'test' | 'remove'

interface AgentEditor {
  base_url: string
  model: string
  apiKey: string
  clearApiKey: boolean
  settings?: AgentModelSettings
  busy?: Action
  feedback?: { type: 'success' | 'error'; message: string }
}

const route = useRoute()
const router = useRouter()
const activeRole = computed<ModelRole>({
  get: () => modelRoles.find((role) => role.id === route.query.agent)?.id ?? 'planner',
  set: (role) => { void router.replace({ query: { ...route.query, agent: role } }) },
})

const modelPlaceholder: Record<ModelRole, string> = {
  planner: '填写命题模型的名称',
  text_reviewer: '填写文本审核模型的名称',
  illustrator: '填写支持 Images API 的模型名称',
  vision_reviewer: '填写支持图片输入的模型名称',
}
const emptyEditor = (): AgentEditor => ({ base_url: '', model: '', apiKey: '', clearApiKey: false })
const editors = reactive<Record<ModelRole, AgentEditor>>({
  planner: emptyEditor(),
  text_reviewer: emptyEditor(),
  illustrator: emptyEditor(),
  vision_reviewer: emptyEditor(),
})
const loading = ref(true)
const loadError = ref('')
const pageController = new AbortController()
const signal = pageController.signal

function resetRole(role: ModelRole, snapshot: ModelSettings) {
  const settings = snapshot.roles?.[role]
  if (!settings) throw new Error('模型配置接口暂不可用，请重新加载。')
  Object.assign(editors[role], emptyEditor(), {
    settings,
    base_url: settings.base_url,
    model: settings.model,
  })
}

function hasChanges(editor: AgentEditor) {
  return editor.base_url !== (editor.settings?.base_url ?? '') ||
    editor.model !== (editor.settings?.model ?? '') ||
    Boolean(editor.apiKey.trim()) ||
    editor.clearApiKey
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const snapshot = await getModelSettings(signal)
    for (const role of modelRoles) resetRole(role.id, snapshot)
  } catch (error) {
    if (!signal.aborted) loadError.value = (error as Error).message
  } finally {
    loading.value = false
  }
}

function requestData(editor: AgentEditor): ModelSettingsUpdate {
  const base_url = editor.base_url.trim()
  const model = editor.model.trim()
  if (!base_url || !model) throw new Error('请填写 API 地址和模型名称。')
  return { base_url, model, api_key: editor.clearApiKey ? '' : editor.apiKey.trim() || undefined }
}

async function runAction(
  role: ModelRole,
  action: Action,
  run: (editor: AgentEditor) => Promise<string | undefined>,
) {
  const editor = editors[role]
  if (editor.busy) return
  editor.feedback = undefined
  editor.busy = action
  try {
    const message = await run(editor)
    if (message && !signal.aborted) editor.feedback = { type: 'success', message }
  } catch (error) {
    if (!signal.aborted) editor.feedback = { type: 'error', message: (error as Error).message }
  } finally {
    editor.busy = undefined
  }
}

function save(role: ModelRole) {
  return runAction(role, 'save', async (editor) => {
    resetRole(role, await saveModelSettings(role, requestData(editor), signal))
    return '模型配置已保存。'
  })
}

function test(role: ModelRole) {
  return runAction(role, 'test', async (editor) => {
    const result = await testModelSettings(role, requestData(editor), signal)
    return result.message
  })
}

function remove(role: ModelRole, label: string) {
  return runAction(role, 'remove', async () => {
    try {
      await ElMessageBox.confirm(`清除后，需重新配置${label}才能使用对应功能。`, '清除模型配置', { type: 'warning' })
    } catch {
      return
    }
    resetRole(role, await deleteModelSettings(role, signal))
    return '模型配置已清除。'
  })
}

onMounted(load)
onUnmounted(() => pageController.abort())
</script>

<style scoped>
.role-status,
.model-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.role-status {
  margin: 4px 0 16px;
}
.field-help {
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}
.test-help {
  margin: 0 0 12px;
}
.model-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}
.retry,
.model-feedback {
  margin-top: 12px;
}
</style>
