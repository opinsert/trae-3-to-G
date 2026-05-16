<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[80vh] overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b bg-blue-50">
        <h2 class="text-xl font-bold text-blue-800">G代码</h2>
        <button @click="close" class="text-gray-500 hover:text-gray-700">
          <svg class="w-6 h-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="flex-1 overflow-auto p-4 max-h-[60vh]">
        <pre class="gcode-textarea whitespace-pre-wrap text-sm font-mono"><code>{{ gcode || '' }}</code></pre>
      </div>

      <div class="p-4 border-t bg-gray-50">
        <div class="flex space-x-3">
          <button
            @click="copyGCode"
            class="flex-1 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors flex items-center justify-center"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
            </svg>
            {{ copied ? '已复制!' : '复制G代码' }}
          </button>
          <button
            @click="validateGCode"
            class="flex-1 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
            在线验证
          </button>
        </div>
      </div>

      <div v-if="validation" class="px-6 py-3 border-t bg-gray-50">
        <div class="flex items-center gap-4">
          <div :class="[
            'px-4 py-2 rounded-full text-sm font-medium',
            validation?.valid ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          ]">
            {{ validation?.valid ? '✓ 验证通过' : '✗ 验证失败' }}
          </div>
          <div v-if="validation?.errors?.length > 0" class="text-red-600 text-sm">
            发现 {{ validation.errors.length }} 个错误
          </div>
          <div v-if="validation?.warnings?.length > 0" class="text-yellow-600 text-sm">
            发现 {{ validation.warnings.length }} 个警告
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  gcode: {
    type: String,
    required: true
  },
  validation: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const copied = ref(false)

const close = () => {
  emit('close')
}

const copyGCode = async () => {
  try {
    await navigator.clipboard.writeText(props.gcode)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (error) {
    console.error('复制失败:', error)
  }
}

const validateGCode = () => {
  const encodedGCode = encodeURIComponent(props.gcode)
  const url = `https://ncviewer.com/?code=${encodedGCode}`
  window.open(url, '_blank')
}
</script>