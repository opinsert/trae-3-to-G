<template>
  <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
    <section class="bg-white rounded-xl shadow-lg flex flex-col h-[600px] overflow-hidden">
      <div class="px-4 py-3 border-b bg-blue-50 flex items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-bold text-blue-800">生成的G代码</h2>
          <p class="text-xs text-blue-600 mt-1">生成结果会在此处显示，可复制后手动粘贴到外部验证工具</p>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="copyGCode"
            class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors text-sm whitespace-nowrap"
          >
            {{ copied ? '已复制!' : '复制G代码' }}
          </button>
          <button
            v-if="manualValidation"
            @click="validateGCode"
            :disabled="isAnimating"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm whitespace-nowrap"
          >
            {{ isAnimating ? '验证中...' : '验证G代码' }}
          </button>
          <button
            v-if="manualValidation"
            @click="completeValidation"
            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm whitespace-nowrap"
          >
            一键完成
          </button>
          <button
            v-if="manualValidation"
            @click="clearValidation"
            class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm whitespace-nowrap"
          >
            清除验证
          </button>
        </div>
      </div>
      <div class="flex-1 overflow-auto bg-gray-50 p-4">
        <pre class="whitespace-pre-wrap text-sm font-mono text-gray-800"><code>{{ gcode || '' }}</code></pre>
      </div>
    </section>

    <section class="bg-white rounded-xl shadow-lg flex flex-col h-[600px] overflow-hidden">
      <div class="px-4 py-3 border-b bg-green-50 flex items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-bold text-green-800">G代码本地验证窗口</h2>
          <p class="text-xs text-green-600 mt-1">在项目内渲染刀路，可在窗口内拖拽旋转、滚轮缩放</p>
        </div>
        <button
          @click="openNcviewer"
          class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm whitespace-nowrap"
        >
          新窗口打开NCViewer
        </button>
      </div>
      <div ref="previewContainer" class="relative flex-1 min-h-0 bg-white">
        <canvas ref="previewCanvas" class="block w-full h-full"></canvas>
        <div
          v-if="manualValidation && !previewRendered && !previewError"
          class="absolute inset-0 flex items-center justify-center bg-white px-6 text-center text-sm text-gray-500"
        >
          点击“验证G代码”后在此处显示刀路预览。
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

const props = defineProps({
  gcode: {
    type: String,
    required: true
  },
  manualValidation: {
    type: Boolean,
    default: false
  }
})

const copied = ref(false)
const previewContainer = ref(null)
const previewCanvas = ref(null)
const previewError = ref('')
const previewRendered = ref(false)
const isAnimating = ref(false)

let preview = null
let resizeObserver = null
let animationTimer = null

const stopAnimation = () => {
  if (animationTimer) {
    clearTimeout(animationTimer)
    animationTimer = null
  }
  isAnimating.value = false
}

const getRenderableLines = () => {
  return props.gcode
    .split('\n')
    .map(line => line.trim())
    .filter(line => line && !line.startsWith(';'))
}

const renderCompletePreview = async () => {
  if (!preview || !props.gcode) return

  try {
    stopAnimation()
    previewError.value = ''
    preview.clear()
    preview.processGCode(props.gcode)
    preview.resize()
    previewRendered.value = true
  } catch (error) {
    console.error('G代码本地预览失败:', error)
    previewError.value = '本地预览失败，请复制G代码后使用外部NCViewer验证。'
  }
}

const renderAnimatedPreview = () => {
  if (!preview || !props.gcode || isAnimating.value) return

  const lines = getRenderableLines()
  if (lines.length === 0) return

  let index = 0

  const step = () => {
    try {
      const partialGcode = lines.slice(0, index + 1).join('\n')
      previewError.value = ''
      preview.clear()
      preview.processGCode(partialGcode)
      preview.resize()
      previewRendered.value = true

      index += 1

      if (index < lines.length) {
        animationTimer = setTimeout(step, 250)
      } else {
        stopAnimation()
      }
    } catch (error) {
      console.error('G代码动画预览失败:', error)
      previewError.value = '动画预览失败，请使用一键完成或外部NCViewer验证。'
      stopAnimation()
    }
  }

  stopAnimation()
  preview.clear()
  previewRendered.value = false
  isAnimating.value = true
  step()
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

  resizeObserver = new ResizeObserver(() => {
    preview?.resize()
  })

  if (previewContainer.value) {
    resizeObserver.observe(previewContainer.value)
  }

  if (!props.manualValidation) {
    renderCompletePreview()
  }
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
  renderAnimatedPreview()
}

const completeValidation = () => {
  renderCompletePreview()
}

const clearValidation = () => {
  stopAnimation()
  preview?.clear()
  previewError.value = ''
  previewRendered.value = false
}

const openNcviewer = () => {
  window.open('https://ncviewer.com/', '_blank')
}

watch(() => props.gcode, () => {
  clearValidation()
  if (!props.manualValidation) {
    renderCompletePreview()
  }
})

onMounted(initPreview)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  stopAnimation()
  preview?.dispose()
  resizeObserver = null
  preview = null
})
</script>
