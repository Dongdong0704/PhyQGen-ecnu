<template>
  <div class="question-preview">
    <section>
      <h4>题干</h4>
      <div
        class="markdown-body"
        v-html="parseMarkdown(question.content || '')"
      />
    </section>
    <section v-if="question.options">
      <h4>选项</h4>
      <div v-if="options" class="options-list">
        <div v-for="(value, key) in options" :key="key" class="option-row">
          <strong>{{ key }}.</strong>
          <div class="markdown-body" v-html="parseMarkdown(value)" />
        </div>
      </div>
      <pre v-else class="raw-options">{{ question.options }}</pre>
    </section>
    <section v-if="question.illustration_url">
      <h4>配图</h4>
      <img
        :key="question.illustration_url"
        :src="question.illustration_url"
        alt="当前习题配图"
        class="question-image"
        @load="imageError = false"
        @error="imageError = true"
      /><el-alert
        v-if="imageError"
        type="error"
        :closable="false"
        title="配图无法预览，请替换图片后再确认定稿。"
      />
    </section>
    <section v-else-if="question.require_illustration">
      <el-alert
        type="warning"
        :closable="false"
        title="本题要求配图，当前图片缺失。请补全后再确认定稿。"
      />
    </section>
    <section>
      <div class="section-heading">
        <h4>答案</h4>
        <el-button
          v-if="!reveal"
          text
          type="primary"
          @click="showAnswer = !showAnswer"
          >{{ showAnswer ? '隐藏答案' : '显示答案' }}</el-button
        >
      </div>
      <div
        v-if="showAnswer || reveal"
        class="markdown-body answer-body"
        v-html="parseMarkdown(question.answer || '')"
      />
    </section>
    <section>
      <div class="section-heading">
        <h4>解析</h4>
        <el-button
          v-if="!reveal"
          text
          type="primary"
          @click="showExplanation = !showExplanation"
          >{{ showExplanation ? '隐藏解析' : '显示解析' }}</el-button
        >
      </div>
      <div
        v-if="showExplanation || reveal"
        class="markdown-body"
        v-html="parseMarkdown(question.explanation || '')"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { parseMarkdown } from '@/utils/markdown'
interface PreviewQuestion {
  content?: string
  options?: string
  answer?: string
  explanation?: string
  illustration_url?: string
  require_illustration?: boolean
}
const props = withDefaults(
  defineProps<{ question: PreviewQuestion; reveal?: boolean }>(),
  { reveal: false },
)
const showAnswer = ref(false)
const showExplanation = ref(false)
const imageError = ref(false)
watch(
  () => props.question.illustration_url,
  () => {
    imageError.value = false
  },
)
const options = computed<Record<string, string> | null>(() => {
  if (!props.question.options) return null
  try {
    const result: unknown = JSON.parse(props.question.options)
    return result &&
      typeof result === 'object' &&
      !Array.isArray(result) &&
      Object.values(result).every((value) => typeof value === 'string')
      ? (result as Record<string, string>)
      : null
  } catch {
    return null
  }
})
</script>

<style scoped>
.question-preview {
  color: #45536d;
  overflow-wrap: anywhere;
}
section {
  margin: 20px 0;
}
h4 {
  font-size: 14px;
  font-weight: 600;
  color: #283b5b;
  margin: 0 0 12px;
}
.markdown-body {
  line-height: 1.9;
  font-size: 14px;
}
.markdown-body :deep(p) {
  margin: 8px 0;
}
.markdown-body :deep(.katex-display) {
  overflow-x: auto;
  overflow-y: hidden;
}
.markdown-body :deep(ul) {
  list-style: disc;
  padding-left: 22px;
}
.markdown-body :deep(ol) {
  list-style: decimal;
  padding-left: 22px;
}
.markdown-body :deep(img) {
  max-width: 100%;
}
.markdown-body :deep(pre) {
  padding: 12px;
  overflow-x: auto;
  background: #eff3f8;
  border-radius: 8px;
}
.option-row {
  display: flex;
  gap: 12px;
  align-items: baseline;
  margin: 8px 0;
}
.option-row > strong {
  color: #4d8ff5;
  flex-shrink: 0;
}
.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.section-heading h4 {
  margin: 0;
}
.answer-body {
  padding: 12px 16px;
  background: #eef7ed;
  border-radius: 7px;
}
.question-image {
  display: block;
  max-width: 100%;
  max-height: 360px;
  object-fit: contain;
  margin: 10px 0;
  background: #fff;
  border: 1px solid #e4ebf5;
  border-radius: 9px;
}
.raw-options {
  white-space: pre-wrap;
  font: inherit;
  line-height: 1.8;
}
</style>
