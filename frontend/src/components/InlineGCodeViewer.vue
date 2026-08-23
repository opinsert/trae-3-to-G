<template>
  <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
    <section class="bg-white rounded-xl shadow-lg flex flex-col h-[600px] overflow-hidden">
      <div class="px-4 py-3 border-b bg-blue-50 flex items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-bold text-blue-800">待审核G代码</h2>
          <p class="text-xs text-blue-600 mt-1">后端规则验证通过后才能复制；仍需人工审核、空运行和试切。</p>
        </div>
        <div class="flex items-center gap-2">
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

    <section class="bg-white rounded-xl shadow-lg flex flex-col h-[600px] overflow-hidden">
      <div class="px-4 py-3 border-b bg-green-50 flex items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-bold text-green-800">本地刀路预览</h2>
          <p class="text-xs text-green-600 mt-1">预览仅用于辅助检查，不进行真实夹具碰撞仿真。</p>
        </div>
        <button
          @click="renderCompletePreview"
          :disabled="!validationState.valid"
          class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed text-sm whitespace-nowrap"
        >
          显示完整刀路
        </button>
      </div>
      <div ref="previewContainer" class="relative flex-1 min-h-0 bg-white">
        <canvas ref="previewCanvas" class="block w-full h-full"></canvas>
        <div
          v-if="!previewRendered && !previewError"
          class="absolute inset-0 flex items-center justify-center bg-white px-6 text-center text-sm text-gray-500"
        >
          {{ validationState.valid ? '点击“显示完整刀路”开始本地预览。' : 'G代码验证失败，已阻止刀路预览。' }}
        </div>
        <div
          v-if="previewError"
          class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90 px-6 text-center text-sm text-red-600"
        >
          {{ previewError }}
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as GCodePreview from 'gcode-preview'
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
const previewContainer = ref(null)
const previewCanvas = ref(null)
const previewError = ref('')
const previewRendered = ref(false)
const validating = ref(false)
const validationState = ref(props.validation)

let preview = null
let resizeObserver = null

const renderCompletePreview = async () => {
  if (!preview || !props.gcode || !validationState.value.valid) return

  try {
    previewError.value = ''
    preview.clear()
    preview.processGCode(props.gcode)
    preview.resize()
    previewRendered.value = true
  } catch (error) {
    console.error('G代码本地预览失败:', error)
    previewError.value = '本地刀路预览失败，请检查G代码格式。'
  }
}

const initPreview = async () => {
  await nextTick()
  if (!previewCanvas.value || preview) return

  preview = GCodePreview.init({
    canvas: previewCanvas.value,
    buildVolume: { x: 200, y: 200, z: 200 },
    initialCameraPosition: [0, 180, 220],
    backgroundColor: '#ffffff',
    extrusionColor: '#16a34a',
    travelColor: '#94a3b8',
    renderTravel: true
  })

  resizeObserver = new ResizeObserver(() => preview?.resize())
  if (previewContainer.value) resizeObserver.observe(previewContainer.value)
}

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
  previewError.value = ''
  try {
    const response = await gcodeApi.validate(props.gcode)
    validationState.value = response.data?.data || { valid: false, errors: [], warnings: [] }
    if (!validationState.value.valid) {
      preview?.clear()
      previewRendered.value = false
    }
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

const clearPreview = () => {
  preview?.clear()
  previewError.value = ''
  previewRendered.value = false
}

watch(() => props.gcode, () => {
  validationState.value = props.validation
  clearPreview()
})

watch(() => props.validation, value => {
  validationState.value = value
}, { deep: true })

onMounted(initPreview)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  preview?.dispose()
  resizeObserver = null
  preview = null
})
</script>
