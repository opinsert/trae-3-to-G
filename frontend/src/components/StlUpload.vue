<template>
  <div class="bg-white rounded-xl shadow-lg p-4 flex flex-col gap-4" style="height: calc(100vh - 160px)">
    <h2 class="text-xl font-bold text-gray-800 shrink-0">STL文件转换</h2>

    <div class="grid grid-cols-2 gap-4 flex-1 min-h-0">
      <div class="border rounded-xl overflow-hidden flex flex-col">
        <div class="px-4 py-2 bg-gray-50 border-b text-sm font-medium text-gray-700 shrink-0">上传STL文件</div>
        <div class="flex-1 flex flex-col items-center justify-center p-4">
          <div
            @click="triggerUpload"
            @dragover.prevent
            @drop.prevent="handleDrop"
            class="w-full border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 hover:bg-blue-50 cursor-pointer transition-all"
          >
            <input ref="fileInput" type="file" accept=".stl,.STL" @change="handleFileSelect" class="hidden" />
            <p class="mt-2 text-sm text-gray-600">点击或拖拽上传STL文件</p>
            <p class="mt-1 text-xs text-gray-400">支持 .stl、.STL 格式，长度单位统一为 mm</p>
          </div>
          <div v-if="stlFileName" class="mt-3 w-full p-2 bg-gray-50 rounded-lg text-sm text-gray-700">已选择：{{ stlFileName }}</div>
          <div class="mt-3 w-full grid grid-cols-3 gap-2">
            <input v-model="tool.name" type="text" placeholder="刀具名称" class="border rounded px-2 py-1 text-sm" />
            <input v-model.number="tool.length" type="number" min="0" placeholder="长度(mm)" class="border rounded px-2 py-1 text-sm" />
            <input v-model.number="tool.diameter" type="number" min="0" placeholder="直径(mm)*" class="border rounded px-2 py-1 text-sm" />
          </div>
          <p class="mt-1 w-full text-xs text-yellow-700">刀具直径缺失时不会生成刀路。</p>
          <button
            @click="fetchOperations"
            :disabled="!stlFile || !hasTool || loadingOps"
            class="mt-2 w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-sm"
          >
            {{ loadingOps ? '生成工序中...' : '生成/刷新工序' }}
          </button>
          <div v-if="loadingOps" class="mt-3 text-sm text-blue-600">正在生成工序...</div>
        </div>
      </div>

      <div class="border rounded-xl overflow-hidden flex flex-col">
        <div class="px-4 py-2 bg-gray-50 border-b text-sm font-medium text-gray-700 shrink-0">模型预览</div>
        <div ref="stlContainer" class="flex-1 relative bg-gray-100">
          <canvas ref="stlCanvas" class="w-full h-full block"></canvas>
          <div v-if="!stlFileName" class="absolute inset-0 flex items-center justify-center text-sm text-gray-400">上传STL文件后显示模型</div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4 flex-1 min-h-0">
      <div class="border rounded-xl overflow-hidden flex flex-col">
        <div class="px-4 py-2 bg-gray-50 border-b flex items-center justify-between shrink-0">
          <span class="text-sm font-medium text-gray-700">加工工序</span>
          <div class="flex gap-2">
            <button v-if="operations.length" @click="copyOperations" class="px-2 py-1 bg-gray-200 text-gray-600 text-xs rounded">{{ opsCopied ? '已复制' : '复制' }}</button>
            <button v-if="operations.length" @click="downloadOperations" class="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">下载CSV</button>
            <button @click="generateGcode" :disabled="!operations.length || loadingGcode || !hasTool" class="px-3 py-1 bg-blue-600 text-white text-sm rounded-lg disabled:opacity-40">{{ loadingGcode ? '生成中...' : '生成待审核G代码' }}</button>
          </div>
        </div>
        <div class="flex-1 overflow-auto">
          <div v-if="!operations.length" class="flex items-center justify-center h-full text-sm text-gray-400">上传文件后自动生成工序</div>
          <table v-else class="w-full text-xs border-collapse">
            <thead class="bg-gray-50 sticky top-0"><tr><th class="border px-2 py-1 text-left">序号</th><th class="border px-2 py-1 text-left">内容</th><th class="border px-2 py-1 text-left">参数</th><th class="border px-2 py-1 text-left">设备</th></tr></thead>
            <tbody><tr v-for="op in operations" :key="op.sequence"><td class="border px-2 py-1">{{ op.sequence }}</td><td class="border px-2 py-1">{{ op.content }}</td><td class="border px-2 py-1 font-mono">{{ op.parameters }}</td><td class="border px-2 py-1">{{ op.equipment }}</td></tr></tbody>
          </table>
        </div>
      </div>

      <div class="border rounded-xl overflow-hidden flex flex-col">
        <div class="px-4 py-2 bg-gray-50 border-b flex items-center justify-between shrink-0">
          <span class="text-sm font-medium text-gray-700">生成的G代码</span>
          <button v-if="gcode && currentValidation.valid" @click="copyGcode" class="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded-lg">{{ copied ? '已复制!' : '复制待审核代码' }}</button>
        </div>
        <div v-if="currentValidation.errors?.length" class="px-3 py-2 bg-red-50 border-b text-xs text-red-700"><p v-for="error in currentValidation.errors" :key="`${error.line}-${error.code}`">第{{ error.line }}行 {{ error.code }}：{{ error.message }}</p></div>
        <div v-if="currentValidation.warnings?.length" class="px-3 py-2 bg-yellow-50 border-b text-xs text-yellow-800"><p v-for="warning in currentValidation.warnings" :key="`${warning.line}-${warning.message}`">第{{ warning.line }}行：{{ warning.message }}</p></div>
        <div class="flex-1 overflow-auto bg-gray-50 p-3"><div v-if="!gcode" class="flex items-center justify-center h-full text-sm text-gray-400">生成后显示G代码</div><pre v-else class="text-xs font-mono text-gray-800 whitespace-pre-wrap">{{ gcode }}</pre></div>
      </div>
    </div>

    <div v-if="recommendedOrder.length > 0" class="border rounded-xl overflow-hidden flex flex-col mt-4" style="max-height: 300px">
      <div class="px-4 py-2 bg-blue-50 border-b flex items-center justify-between shrink-0"><span class="text-sm font-medium text-blue-800">分方向加工 ({{ recommendedOrder.length }}个方向{{ directionSource === 'ai' ? ' - AI推荐顺序' : '' }})</span><span class="text-xs text-blue-600">{{ directionExplanation }}</span></div>
      <div class="flex border-b bg-gray-50 shrink-0 overflow-x-auto"><button v-for="dir in recommendedOrder" :key="dir" @click="activeDirection = dir" :class="['px-4 py-2 text-sm whitespace-nowrap border-r', activeDirection === dir ? 'bg-white text-blue-700 font-medium border-b-2 border-b-blue-500' : 'text-gray-600']">{{ directionLabels[dir] || dir }}</button></div>
      <div class="flex-1 overflow-auto bg-gray-50 p-3"><div v-if="directionGcodes[activeDirection]" class="space-y-2"><div class="flex items-center justify-between text-xs text-gray-500"><span>{{ directionGcodes[activeDirection].split('\n').length }} 行</span><button v-if="directionValidations[activeDirection]?.valid" @click="copyDirectionGcode(activeDirection)" class="px-2 py-0.5 bg-gray-200 rounded text-xs">{{ copiedDir === activeDirection ? '已复制' : '复制待审核代码' }}</button></div><pre class="text-xs font-mono text-gray-800 whitespace-pre-wrap">{{ directionGcodes[activeDirection] }}</pre></div><div v-else class="flex items-center justify-center h-full text-sm text-gray-400">生成后显示该方向G代码</div></div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import * as THREE from 'three'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { stlApi, gcodeApi } from '../api'

const fileInput = ref(null)
const stlFileName = ref('')
const stlFile = ref('')
const operations = ref([])
const gcode = ref('')
const loadingOps = ref(false)
const loadingGcode = ref(false)
const copied = ref(false)
const copiedDir = ref('')
const opsCopied = ref(false)
const stlCanvas = ref(null)
const stlContainer = ref(null)
const tool = ref({ name: '立铣刀（仿真）', length: 75, diameter: null })
const currentValidation = ref({ valid: false, errors: [], warnings: [] })
const directionValidations = ref({})

const recommendedOrder = ref([])
const activeDirection = ref('+Z')
const directionExplanation = ref('')
const directionSource = ref('')
const directionLabels = { '+Z': '顶面', '-Z': '底面', '+X': '右面', '-X': '左面', '+Y': '前面', '-Y': '后面' }
const directionGcodes = ref({})
const hasTool = computed(() => Number.isFinite(Number(tool.value.diameter)) && Number(tool.value.diameter) > 0)

let renderer = null
let animFrameId = null
let objectUrl = null
let controls = null

const triggerUpload = () => fileInput.value?.click()
const handleFileSelect = (e) => processFile(e.target.files?.[0])
const handleDrop = (e) => processFile(e.dataTransfer?.files?.[0])

const processFile = async (file) => {
  if (!file || !file.name.toLowerCase().endsWith('.stl')) return
  stlFileName.value = file.name
  operations.value = []
  gcode.value = ''
  currentValidation.value = { valid: false, errors: [], warnings: [] }
  directionGcodes.value = {}
  directionValidations.value = {}
  recommendedOrder.value = []
  activeDirection.value = '+Z'
  directionExplanation.value = ''
  directionSource.value = ''

  const reader = new FileReader()
  reader.onload = async (e) => {
    stlFile.value = e.target.result.split(',')[1] || ''
    await fetchOperations()
  }
  reader.onerror = () => {
    console.error('[前端-STL] 文件读取失败:', reader.error)
    alert('STL文件读取失败，请重试')
    stlFileName.value = ''
  }
  reader.readAsDataURL(file)
  renderStl(file)
}

const defaultProcessCard = () => ({
  product_name: stlFileName.value.replace(/\.stl$/i, ''), process_name: 'STL加工', process_number: '001', version: 'A', equipment: '三轴加工中心（仿真）', control_system: 'FANUC-compatible', fixture: '通用夹具（仿真）', material: '未指定材料（仿真）', tool_info: { name: tool.value.name, length: Number(tool.value.length) || 75, diameter: Number(tool.value.diameter) || 0 }
})

const fetchOperations = async () => {
  if (!hasTool.value) return
  loadingOps.value = true
  try {
    const card = defaultProcessCard()
    const res = await stlApi.convert(stlFile.value, card, '+Z')
    if (res.data.success) operations.value = res.data.data.operations || []
    await fetchDirectionPlan(card)
  } catch (e) {
    console.error('工序生成失败:', e)
    alert(`工序生成失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    loadingOps.value = false
  }
}

const fetchDirectionPlan = async (card) => {
  try {
    const res = await stlApi.planDirections(stlFile.value, card)
    if (res.data.success) {
      const directions = res.data.directions || {}
      recommendedOrder.value = res.data.recommended_order || Object.keys(directions)
      directionExplanation.value = res.data.explanation || ''
      directionSource.value = res.data.source || ''
      if (recommendedOrder.value.length) activeDirection.value = recommendedOrder.value[0]
    }
  } catch (e) {
    console.error('方向规划失败:', e)
  }
}

const generateGcode = async () => {
  if (!hasTool.value) return
  loadingGcode.value = true
  currentValidation.value = { valid: false, errors: [], warnings: [] }
  try {
    const card = defaultProcessCard()
    const res = await stlApi.generateGcode(stlFile.value, card, operations.value, '+Z')
    if (res.data.success) {
      gcode.value = res.data.data.gcode || ''
      currentValidation.value = res.data.data.validation || { valid: false, errors: [], warnings: [] }
    }
    await generateAllDirectionGcodes(card)
  } catch (e) {
    console.error('G代码生成失败:', e)
    alert(`G代码生成失败: ${e.response?.data?.detail || e.message}`)
  } finally {
    loadingGcode.value = false
  }
}

const generateAllDirectionGcodes = async (card) => {
  for (const dir of recommendedOrder.value) {
    try {
      if (dir === '+Z' && gcode.value) {
        directionGcodes.value[dir] = gcode.value
        directionValidations.value[dir] = currentValidation.value
        continue
      }
      const dirRes = await stlApi.convert(stlFile.value, card, dir)
      if (!dirRes.data.success) continue
      const ops = dirRes.data.data.operations || []
      const gRes = await stlApi.generateGcode(stlFile.value, card, ops, dir)
      if (gRes.data.success) {
        const code = gRes.data.data.gcode || ''
        directionGcodes.value[dir] = code
        directionValidations.value[dir] = gRes.data.data.validation || await validateCode(code)
      }
    } catch (e) {
      console.error(`方向${dir} G代码生成失败:`, e)
    }
  }
}

const validateCode = async (code) => {
  const response = await gcodeApi.validate(code)
  return response.data?.data || { valid: false, errors: [], warnings: [] }
}

const copyDirectionGcode = async (dir) => {
  if (!directionValidations.value[dir]?.valid) return
  await navigator.clipboard.writeText(directionGcodes.value[dir])
  copiedDir.value = dir
  setTimeout(() => { copiedDir.value = '' }, 2000)
}

const copyGcode = async () => {
  if (!currentValidation.value.valid) return
  await navigator.clipboard.writeText(gcode.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

const copyOperations = async () => {
  const header = '序号\t内容\t参数\t设备\t备注'
  const rows = operations.value.map(op => `${op.sequence}\t${op.content}\t${op.parameters}\t${op.equipment}\t${op.remark || ''}`)
  await navigator.clipboard.writeText([header, ...rows].join('\n'))
  opsCopied.value = true
  setTimeout(() => { opsCopied.value = false }, 2000)
}

const downloadOperations = () => {
  const header = '序号,内容,参数,设备,备注'
  const rows = operations.value.map(op => `"${op.sequence}","${op.content}","${op.parameters}","${op.equipment}","${op.remark || ''}"`)
  const blob = new Blob(['\uFEFF' + [header, ...rows].join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `STL工序表_${stlFileName.value.replace(/\.\w+$/i, '')}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

const renderStl = (file) => {
  if (objectUrl) URL.revokeObjectURL(objectUrl)
  objectUrl = URL.createObjectURL(file)
  const canvas = stlCanvas.value
  const container = stlContainer.value
  if (!canvas || !container) return
  if (renderer) {
    renderer.dispose()
    controls?.dispose()
    cancelAnimationFrame(animFrameId)
  }
  const w = container.clientWidth || 400
  const h = container.clientHeight || 300
  const scene = new THREE.Scene()
  scene.background = new THREE.Color(0xf3f4f6)
  const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 10000)
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true })
  renderer.setSize(w, h)
  renderer.setPixelRatio(window.devicePixelRatio)
  scene.add(new THREE.AmbientLight(0xffffff, 0.6))
  const light = new THREE.DirectionalLight(0xffffff, 0.8)
  light.position.set(1, 2, 3)
  scene.add(light)
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  new STLLoader().load(objectUrl, geo => {
    geo.computeBoundingBox()
    const center = new THREE.Vector3()
    geo.boundingBox.getCenter(center)
    geo.translate(-center.x, -center.y, -center.z)
    const size = new THREE.Vector3()
    geo.boundingBox.getSize(size)
    camera.position.set(0, 0, Math.max(size.x, size.y, size.z) * 2)
    controls.update()
    scene.add(new THREE.Mesh(geo, new THREE.MeshPhongMaterial({ color: 0x6366f1, specular: 0x333333 })))
  })
  const animate = () => {
    animFrameId = requestAnimationFrame(animate)
    controls.update()
    renderer.render(scene, camera)
  }
  animate()
}

onBeforeUnmount(() => {
  renderer?.dispose()
  controls?.dispose()
  cancelAnimationFrame(animFrameId)
  if (objectUrl) URL.revokeObjectURL(objectUrl)
})
</script>
