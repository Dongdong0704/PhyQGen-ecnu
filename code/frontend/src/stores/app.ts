import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  const collapsedByUser = ref(false)
  const viewportWidth = ref(window.innerWidth)
  window.addEventListener('resize', () => {
    viewportWidth.value = window.innerWidth
  })
  const sidebarCollapsed = computed(
    () => viewportWidth.value <= 700 || collapsedByUser.value,
  )

  function toggleSidebar() {
    collapsedByUser.value = !collapsedByUser.value
  }

  return {
    sidebarCollapsed,
    toggleSidebar,
  }
})
