<template>
  <div class="settings-container">
    <el-card class="header-card">
      <div class="page-header">
        <div class="title-section">
          <el-tag type="info" size="small" effect="plain">管理员工作台</el-tag>
          <h2>系统维护</h2>
          <p class="subtitle">配置模型、知识库与任务执行参数，查看维护记录。</p>
        </div>
        <el-button
          type="primary"
          :icon="Check"
          :loading="saving"
          @click="handleSave"
          >保存配置</el-button
        >
      </div>
    </el-card>

    <el-alert
      title="当前为前端演示环境"
      type="info"
      :closable="false"
      show-icon
    >
      连接测试、索引重建和模型调用均为本地模拟，不发送网络请求。请勿填写真实密钥；配置和记录保存在当前浏览器。
    </el-alert>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-row :gutter="20">
        <el-col :xs="24" :lg="14">
          <el-card class="config-card">
            <template #header>
              <div class="card-header">
                <span
                  ><el-icon><Connection /></el-icon> 模型连接配置</span
                ><el-tag type="info" size="small">模拟服务</el-tag>
              </div>
            </template>
            <el-form-item label="文本模型" prop="text_model"
              ><el-input
                v-model="form.text_model"
                placeholder="请输入文本生成与校验模型名称"
                maxlength="120"
            /></el-form-item>
            <el-form-item label="图像模型" prop="image_model"
              ><el-input
                v-model="form.image_model"
                placeholder="请输入配图与图文校验模型名称"
                maxlength="120"
            /></el-form-item>
            <el-form-item label="嵌入模型" prop="embedding_model"
              ><el-input
                v-model="form.embedding_model"
                placeholder="请输入知识检索嵌入模型名称"
                maxlength="120"
            /></el-form-item>
            <el-form-item label="服务地址（仅保存配置）" prop="endpoint"
              ><el-input
                v-model="form.endpoint"
                placeholder="http://localhost:8000"
                maxlength="300"
            /></el-form-item>
            <div class="test-row">
              <el-button
                :icon="Connection"
                :loading="testing"
                @click="handleTest"
                >模拟连接测试</el-button
              ><span class="helper-text">不验证真实服务可用性</span>
            </div>
            <el-alert
              v-if="testMessage"
              :title="testMessage"
              type="info"
              :closable="false"
              show-icon
              class="test-result"
            />
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="10">
          <el-card class="config-card">
            <template #header
              ><div class="card-header">
                <span
                  ><el-icon><Collection /></el-icon> 知识库索引</span
                ><el-tag
                  :type="
                    prototypeState.settings.kb_enabled &&
                    prototypeState.settings.kb_status === '可用'
                      ? 'success'
                      : 'info'
                  "
                  size="small"
                  >{{
                    prototypeState.settings.kb_enabled
                      ? prototypeState.settings.kb_status
                      : '已停用'
                  }}</el-tag
                >
              </div></template
            >
            <div class="switch-row">
              <span>启用知识库服务</span
              ><el-switch
                v-model="form.kb_enabled"
                inline-prompt
                active-text="开"
                inactive-text="关"
              />
            </div>
            <p class="helper-text">
              修改开关后点击“保存配置”生效；停用时出题按普通生成流程继续。
            </p>
            <el-descriptions :column="1" border class="kb-descriptions">
              <el-descriptions-item label="当前索引版本">{{
                prototypeState.settings.kb_version
              }}</el-descriptions-item>
              <el-descriptions-item label="演示片段"
                >{{
                  prototypeState.settings.kb_fragments
                }}
                条</el-descriptions-item
              >
              <el-descriptions-item label="资料范围"
                >运动与力、电路、机械能</el-descriptions-item
              >
            </el-descriptions>
            <el-button
              :icon="Refresh"
              :loading="rebuilding"
              @click="handleRebuild"
              >演示重建索引</el-button
            >
            <p class="helper-text rebuild-note">
              重建仅更新演示索引版本与3条预置片段的计数，不处理真实资料。
            </p>
          </el-card>
          <el-card class="config-card">
            <template #header
              ><div class="card-header">
                <span
                  ><el-icon><Operation /></el-icon> 任务执行配置</span
                >
              </div></template
            >
            <el-form-item label="逐题并发上限" prop="concurrency"
              ><el-input-number
                v-model="form.concurrency"
                :min="1"
                :max="5"
                :step="1"
                step-strictly
              /><span class="number-hint">1～5 道</span></el-form-item
            >
            <el-form-item label="单题最大轮次（含首次）" prop="max_rounds"
              ><el-input-number
                v-model="form.max_rounds"
                :min="1"
                :max="3"
                :step="1"
                step-strictly
              /><span class="number-hint">1～3 轮</span></el-form-item
            >
            <p class="helper-text">
              用于演示任务编排与异常终止。教师编辑、确认定稿不会触发智能体重试。
            </p>
          </el-card>
        </el-col>
      </el-row>
    </el-form>

    <el-card class="audit-card">
      <template #header
        ><div class="card-header">
          <span
            ><el-icon><Clock /></el-icon> 维护操作记录</span
          ><span class="helper-text"
            >共 {{ prototypeState.audits.length }} 条</span
          >
        </div></template
      >
      <el-table
        :data="visibleAudits"
        empty-text="暂无维护记录，保存配置或执行演示测试后会在这里显示。"
        stripe
      >
        <el-table-column label="操作内容" prop="action" min-width="250" />
        <el-table-column label="操作者" prop="actor" width="140" />
        <el-table-column label="时间" min-width="180"
          ><template #default="{ row }">{{
            formatTime(row.time)
          }}</template></el-table-column
        >
      </el-table>
      <el-pagination
        v-if="prototypeState.audits.length > 10"
        v-model:current-page="auditPage"
        :total="prototypeState.audits.length"
        :page-size="10"
        layout="prev, pager, next"
        class="audit-pagination"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  Check,
  Clock,
  Collection,
  Connection,
  Operation,
  Refresh,
} from '@element-plus/icons-vue'
import {
  audit,
  commit,
  prototypeState,
  requireAdmin,
  saveSettings,
} from '@/prototype/store'
import type { Settings } from '@/prototype/types'

const form = reactive<Settings>(
  JSON.parse(JSON.stringify(prototypeState.settings)),
)
const formRef = ref<FormInstance>()
const saving = ref(false)
const testing = ref(false)
const rebuilding = ref(false)
const testMessage = ref('')
const auditPage = ref(1)
const visibleAudits = computed(() =>
  prototypeState.audits.slice((auditPage.value - 1) * 10, auditPage.value * 10),
)
const rules: FormRules = {
  text_model: [
    {
      required: true,
      whitespace: true,
      message: '请输入文本模型名称',
      trigger: 'blur',
    },
  ],
  image_model: [
    {
      required: true,
      whitespace: true,
      message: '请输入图像模型名称',
      trigger: 'blur',
    },
  ],
  embedding_model: [
    {
      required: true,
      whitespace: true,
      message: '请输入嵌入模型名称',
      trigger: 'blur',
    },
  ],
  endpoint: [
    { required: true, message: '请输入服务地址', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        try {
          const url = new URL(value)
          if (
            !['http:', 'https:'].includes(url.protocol) ||
            url.username ||
            url.password
          )
            throw new Error()
          callback()
        } catch {
          callback(
            new Error('请输入有效的 http/https 地址，地址中不要包含账号或密码'),
          )
        }
      },
      trigger: 'blur',
    },
  ],
  concurrency: [
    {
      type: 'integer',
      required: true,
      min: 1,
      max: 5,
      message: '并发上限须为1～5的整数',
      trigger: 'change',
    },
  ],
  max_rounds: [
    {
      type: 'integer',
      required: true,
      min: 1,
      max: 3,
      message: '最大轮次须为1～3的整数',
      trigger: 'change',
    },
  ],
}
const delay = (ms: number) =>
  new Promise((resolve) => window.setTimeout(resolve, ms))
const formatTime = (value: string) =>
  new Date(value).toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    hour12: false,
  })
const reportError = (error: unknown) =>
  ElMessage.error(error instanceof Error ? error.message : '操作失败，请重试')

async function handleSave() {
  if (!(await formRef.value?.validate().catch(() => false))) return
  saving.value = true
  try {
    saveSettings(form)
    auditPage.value = 1
    ElMessage.success('配置已保存到当前浏览器')
  } catch (error) {
    reportError(error)
  } finally {
    saving.value = false
  }
}
async function handleTest() {
  if (!(await formRef.value?.validate().catch(() => false))) return
  testing.value = true
  testMessage.value = ''
  try {
    requireAdmin()
    await delay(500)
    commit(() =>
      audit(
        `模拟连接测试：${form.text_model} / ${form.image_model} / ${form.embedding_model}（未发送网络请求）`,
      ),
    )
    auditPage.value = 1
    testMessage.value =
      '模拟测试完成：配置格式有效，演示适配器可用。真实模型连接尚未验证。'
    ElMessage.info('模拟连接测试完成')
  } catch (error) {
    reportError(error)
  } finally {
    testing.value = false
  }
}
async function handleRebuild() {
  rebuilding.value = true
  try {
    requireAdmin()
    await delay(650)
    commit(() => {
      prototypeState.settings.kb_version = `demo-index-${Date.now()}`
      prototypeState.settings.kb_fragments = 3
      prototypeState.settings.kb_status = '可用'
      audit('演示重建知识库索引：3条预置片段，未处理真实资料')
    })
    form.kb_version = prototypeState.settings.kb_version
    form.kb_fragments = 3
    form.kb_status = '可用'
    auditPage.value = 1
    ElMessage.success('演示索引已更新，当前有3条预置片段')
  } catch (error) {
    reportError(error)
  } finally {
    rebuilding.value = false
  }
}
</script>

<style scoped>
.settings-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.page-header,
.card-header,
.switch-row,
.test-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.title-section h2 {
  margin: 10px 0 6px;
  font-size: 24px;
}
.subtitle,
.helper-text {
  color: var(--color-text-secondary);
  line-height: 1.7;
}
.helper-text {
  font-size: 12px;
}
.config-card {
  margin-bottom: 20px;
}
.card-header {
  font-weight: 600;
}
.card-header > span:first-child {
  display: flex;
  align-items: center;
  gap: 7px;
}
.test-row {
  justify-content: flex-start;
  flex-wrap: wrap;
}
.test-result {
  margin-top: 16px;
}
.kb-descriptions {
  margin: 18px 0;
}
.rebuild-note {
  margin-top: 10px;
}
.number-hint {
  margin-left: 12px;
  color: var(--color-text-secondary);
}
.audit-pagination {
  justify-content: flex-end;
  margin-top: 18px;
}
@media (max-width: 640px) {
  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }
  .settings-container {
    gap: 14px;
  }
  .number-hint {
    display: block;
    margin: 7px 0 0;
  }
}
</style>
