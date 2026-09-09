<template>
  <section class="mt-8 bg-white rounded-xl shadow-lg flex flex-col overflow-hidden" style="height: 520px">
    <div class="px-4 py-3 border-b bg-blue-50 flex items-center justify-between gap-3">
      <div>
        <h2 class="text-lg font-bold text-blue-800">待审核G代码</h2>
        <p class="text-xs text-blue-600 mt-1">后端规则验证通过后才能复制；仍需人工审核、空运行和试切。</p>
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <span :class="[
          'px-3 py-1 rounded-full text-xs font-medium',
          validationState.valid ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
        ]">
          {{ validationState.valid ? '规则验证通过' : '规则验证失败' }}
        </span>
        <button
          @click="validateGCode"
          :disabled="validating"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm whitespace-nowrap"
        >
          {{ validating ? '验证中...' : '重新验证' }}
        </button>
        <button
          @click="copyGCode"
          :disabled="!validationState.valid"
          class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-40 disabled:cursor-not-allowed text-sm whitespace-nowrap"
        >
          {{ copied ? '已复制!' : '复制待审核代码' }}
        </button>
      </div>
    </div>
    <div v-if="validationState.errors?.length" class="px-4 py-3 bg-red-50 border-b text-sm text-red-700">
      <p v-for="error in validationState.errors" :key="`${error.line}-${error.code}`">
        第{{ error.line }}行 {{ error.code }}：{{ error.message }}
      </p>
    </div>
    <div v-if="validationState.warnings?.length" class="px-4 py-3 bg-yellow-50 border-b text-sm text-yellow-800">
      <p v-for="warning in validationState.warnings" :key="`${warning.line}-${warning.message}`">
        第{{ warning.line }}行：{{ warning.message }}
      </p>
    </div>
    <div class="flex-1 overflow-auto bg-gray-50 p-4">
      <pre class="whitespace-pre-wrap text-sm font-mono text-gray-800"><code>{{ gcode }}</code></pre>
    </div>
  </section>
</template>

<script setup>
import { ref, watch } from 'vue'
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

const copied = ref(false)
const validating = ref(false)
const validationState = ref(props.validation)

const copyGCode = async () => {
  if (!validationState.value.valid) return
  try {
    await navigator.clipboard.writeText(props.gcode)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch (error) {
    console.error('复制失败:', error)
  }
}

const validateGCode = async () => {
  validating.value = true
  try {
    const response = await gcodeApi.validate(props.gcode)
    validationState.value = response.data?.data || { valid: false, errors: [], warnings: [] }
  } catch (error) {
    validationState.value = {
      valid: false,
      errors: [{ line: 0, code: 'REQUEST', message: error.response?.data?.detail || 'G代码验证请求失败' }],
      warnings: []
    }
  } finally {
    validating.value = false
  }
}

watch(() => props.gcode, () => {
  validationState.value = props.validation
})

watch(() => props.validation, (value) => {
  validationState.value = value
}, { deep: true })
</script>
