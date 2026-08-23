<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl shadow-2xl max-w-[95vw] w-full h-[85vh] overflow-hidden flex flex-col">
      <div class="flex items-center justify-between px-6 py-4 border-b bg-blue-50">
        <h2 class="text-xl font-bold text-blue-800">待审核G代码</h2>
        <button @click="close" class="text-gray-500 hover:text-gray-700">
          <svg class="w-6 h-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="flex-1 overflow-hidden p-4 min-h-0">
        <div class="h-full overflow-auto border rounded-lg bg-gray-50 p-3">
          <pre class="gcode-textarea whitespace-pre-wrap text-sm font-mono"><code>{{ gcode || '' }}</code></pre>
        </div>
      </div>

      <div class="p-4 border-t bg-gray-50">
        <div class="flex space-x-3">
          <button
            @click="copyGCode"
            :disabled="!localValidation.valid"
            class="flex-1 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {{ copied ? '已复制!' : '复制待审核代码' }}
          </button>
          <button
            @click="validateGCode"
            :disabled="validating"
            class="flex-1 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            {{ validating ? '验证中...' : '重新验证' }}
          </button>
        </div>
      </div>

      <div class="px-6 py-3 border-t bg-gray-50">
        <div class="flex items-center gap-4">
          <div :class="[
            'px-4 py-2 rounded-full text-sm font-medium',
            localValidation.valid ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          ]">
            {{ localValidation.valid ? '验证通过' : '验证失败' }}
          </div>
          <div v-if="localValidation.errors.length" class="text-red-600 text-sm">
            发现 {{ localValidation.errors.length }} 个错误
          </div>
          <div v-if="localValidation.warnings.length" class="text-yellow-600 text-sm">
            发现 {{ localValidation.warnings.length }} 个警告
          </div>
        </div>
        <div v-if="localValidation.errors.length" class="mt-2 text-sm text-red-700">
          <p v-for="error in localValidation.errors" :key="`${error.line}-${error.code}`">
            第{{ error.line }}行 {{ error.code }}：{{ error.message }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { gcodeApi } from '../api'

const props = defineProps({
  gcode: {
    type: String,
    required: true
  },
  validation: {
    type: Object,
    default: () => ({ valid: false, errors: [], warnings: [] })
  }
})

const emit = defineEmits(['close'])

const copied = ref(false)
const validating = ref(false)
const localValidation = ref({
  valid: props.validation?.valid === true,
  errors: props.validation?.errors || [],
  warnings: props.validation?.warnings || []
})

const close = () => {
  emit('close')
}

const copyGCode = async () => {
  if (!localValidation.value.valid) return
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

const validateGCode = async () => {
  validating.value = true
  try {
    const response = await gcodeApi.validate(props.gcode)
    localValidation.value = response.data?.data || { valid: false, errors: [], warnings: [] }
  } catch (error) {
    localValidation.value = {
      valid: false,
      errors: [{ line: 0, code: 'REQUEST', message: error.response?.data?.detail || 'G代码验证请求失败' }],
      warnings: []
    }
  } finally {
    validating.value = false
  }
}
</script>
