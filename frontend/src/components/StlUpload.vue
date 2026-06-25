<template>
  <div class="bg-white rounded-xl shadow-lg p-4 flex flex-col gap-4" style="height: calc(100vh - 160px)">
    <h2 class="text-xl font-bold text-gray-800 shrink-0">STL文件转换</h2>

    <!-- 上半行：上传 + 3D预览 -->
    <div class="grid grid-cols-2 gap-4 flex-1 min-h-0">
      <!-- 左上：文件上传 -->
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
            <svg class="mx-auto h-12 w-12 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p class="mt-2 text-sm text-gray-600">点击或拖拽上传STL文件</p>
            <p class="mt-1 text-xs text-gray-400">支持 .stl、.STL 格式</p>
          </div>
          <div v-if="stlFileName" class="mt-3 w-full p-2 bg-gray-50 rounded-lg text-sm text-gray-700">已选择：{{ stlFileName }}</div>
          <div v-if="loadingOps" class="mt-3 text-sm text-blue-600">正在生成工序...</div>
        </div>
      </div>

      <!-- 右上：STL 3D预览 -->
      <div class="border rounded-xl overflow-hidden flex flex-col">
        <div class="px-4 py-2 bg-gray-50 border-b text-sm font-medium text-gray-700 shrink-0">模型预览</div>
        <div ref="stlContainer" class="flex-1 relative bg-gray-100">
          <canvas ref="stlCanvas" class="w-full h-full block"></canvas>
          <div v-if="!stlFileName" class="absolute inset-0 flex items-center justify-center text-sm text-gray-400">上传STL文件后显示模型</div>
        </div>
      </div>
    </div>

    <!-- 下半行：工序列表 + G代码 -->
    <div class="grid grid-cols-2 gap-4 flex-1 min-h-0">
      <!-- 左下：工序列表 -->
      <div class="border rounded-xl overflow-hidden flex flex-col">
        <div class="px-4 py-2 bg-gray-50 border-b flex items-center justify-between shrink-0">
          <span class="text-sm font-medium text-gray-700">加工工序</span>
          <div class="flex gap-2">
            <button
              v-if="operations.length"
              @click="copyOperations"
              class="px-2 py-1 bg-gray-200 text-gray-600 text-xs rounded hover:bg-gray-300 transition-colors"
            >
              {{ opsCopied ? '已复制' : '复制' }}
            </button>
            <button
              v-if="operations.length"
              @click="downloadOperations"
              class="px-2 py-1 bg-green-100 text-green-700 text-xs rounded hover:bg-green-200 transition-colors"
            >
              下载CSV
            </button>
            <button
              @click="generateGcode"
              :disabled="!operations.length || loadingGcode"
              class="px-3 py-1 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {{ loadingGcode ? '生成中...' : '生成工序图表格' }}
            </button>
          </div>
        </div>
        <div class="flex-1 overflow-auto">
          <div v-if="!operations.length" class="flex items-center justify-center h-full text-sm text-gray-400">上传文件后自动生成工序</div>
          <table v-else class="w-full text-xs border-collapse">
            <thead class="bg-gray-50 sticky top-0">
              <tr>
                <th class="border px-2 py-1 text-left w-8">序号</th>
                <th class="border px-2 py-1 text-left">内容</th>
                <th class="border px-2 py-1 text-left">参数</th>
                <th class="border px-2 py-1 text-left">设备</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="op in operations" :key="op.sequence" class="hover:bg-gray-50">
                <td class="border px-2 py-1">{{ op.sequence }}</td>
                <td class="border px-2 py-1">{{ op.content }}</td>
                <td class="border px-2 py-1 font-mono">{{ op.parameters }}</td>
                <td class="border px-2 py-1">{{ op.equipment }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 右下：G代码 -->
      <div class="border rounded-xl overflow-hidden flex flex-col">
        <div class="px-4 py-2 bg-gray-50 border-b flex items-center justify-between shrink-0">
          <span class="text-sm font-medium text-gray-700">生成的G代码</span>
          <div v-if="gcode" class="flex gap-2">
            <button
              @click="copyGcode"
              class="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 transition-colors"
            >
              {{ copied ? '已复制!' : '复制' }}
            </button>
            <button
              @click="validateOnline"
              class="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-lg hover:bg-blue-200 transition-colors"
            >
              在线验证
            </button>
          </div>
        </div>
        <div class="flex-1 overflow-auto bg-gray-50 p-3">
          <div v-if="!gcode" class="flex items-center justify-center h-full text-sm text-gray-400">点击「生成工序图表格」后显示G代码</div>
          <pre v-else class="text-xs font-mono text-gray-800 whitespace-pre-wrap">{{ gcode }}</pre>
        </div>
      </div>
    </div>

    <!-- 分方向G代码面板 -->
    <div v-if="directionPlans.length > 0" class="border rounded-xl overflow-hidden flex flex-col mt-4" style="max-height: 300px">
      <div class="px-4 py-2 bg-blue-50 border-b flex items-center justify-between shrink-0">
        <span class="text-sm font-medium text-blue-800">
          分方向加工 ({{ recommendedOrder.length }}个方向{{ directionSource === 'deepseek' ? ' - DeepSeek推荐顺序' : '' }})
        </span>
        <span class="text-xs text-blue-600">{{ directionExplanation }}</span>
      </div>
      <!-- 方向tabs -->
      <div class="flex border-b bg-gray-50 shrink-0 overflow-x-auto">
        <button
          v-for="dir in recommendedOrder"
          :key="dir"
          @click="activeDirection = dir"
          :class="[
            'px-4 py-2 text-sm whitespace-nowrap border-r transition-colors',
            activeDirection === dir
              ? 'bg-white text-blue-700 font-medium border-b-2 border-b-blue-500'
              : 'text-gray-600 hover:bg-gray-100'
          ]"
        >
          {{ directionLabels[dir] || dir }}
        </button>
      </div>
      <!-- 当前方向G代码 -->
      <div class="flex-1 overflow-auto bg-gray-50 p-3">
        <div v-if="directionGcodes[activeDirection]" class="space-y-2">
          <div class="flex items-center justify-between text-xs text-gray-500 mb-1">
            <span>{{ directionGcodes[activeDirection].split('\n').length }} 行</span>
            <div class="flex gap-2">
              <button @click="copyDirectionGcode(activeDirection)" class="px-2 py-0.5 bg-gray-200 rounded hover:bg-gray-300 text-xs">
                {{ copiedDir === activeDirection ? '已复制' : '复制' }}
              </button>
              <button @click="validateDirectionOnline(activeDirection)" class="px-2 py-0.5 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-xs">
                在线验证
              </button>
            </div>
          </div>
          <pre class="text-xs font-mono text-gray-800 whitespace-pre-wrap">{{ directionGcodes[activeDirection] }}</pre>
        </div>
        <div v-else class="flex items-center justify-center h-full text-sm text-gray-400">
          点击「生成工序图表格」后自动生成各方向G代码
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref } from 'vue'
import * as THREE from 'three'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { stlApi } from '../api'

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

// direction support
const directionPlans = ref([])
const directionGcodes = ref({})
const recommendedOrder = ref([])
const activeDirection = ref('+Z')
const directionExplanation = ref('')
const directionSource = ref('')
const directionLabels = {
  '+Z': '顶面', '-Z': '底面',
  '+X': '右面', '-X': '左面',
  '+Y': '前面', '-Y': '后面',
}

let renderer = null
let animFrameId = null
let objectUrl = null
let controls = null

const triggerUpload = () => fileInput.value?.click()

const processFile = async (file) => {
  if (!file || !file.name.toLowerCase().endsWith('.stl')) return
  stlFileName.value = file.name
  operations.value = []
  gcode.value = ''

  // base64 for API
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

  // 3D preview
  renderStl(file)
}

const handleFileSelect = (e) => processFile(e.target.files?.[0])
const handleDrop = (e) => processFile(e.dataTransfer?.files?.[0])

const renderStl = (file) => {
  if (objectUrl) URL.revokeObjectURL(objectUrl)
  objectUrl = URL.createObjectURL(file)

  const canvas = stlCanvas.value
  const container = stlContainer.value
  if (!canvas || !container) return

  // dispose previous renderer
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
  const dir = new THREE.DirectionalLight(0xffffff, 0.8)
  dir.position.set(1, 2, 3)
  scene.add(dir)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true

  new STLLoader().load(objectUrl, (geo) => {
    geo.computeBoundingBox()
    const center = new THREE.Vector3()
    geo.boundingBox.getCenter(center)
    geo.translate(-center.x, -center.y, -center.z)

    const size = new THREE.Vector3()
    geo.boundingBox.getSize(size)
    const maxDim = Math.max(size.x, size.y, size.z)
    camera.position.set(0, 0, maxDim * 2)
    controls.update()

    const mesh = new THREE.Mesh(geo, new THREE.MeshPhongMaterial({ color: 0x6366f1, specular: 0x333333 }))
    scene.add(mesh)
  })

  const animate = () => {
    animFrameId = requestAnimationFrame(animate)
    controls.update()
    renderer.render(scene, camera)
  }
  animate()
}

const fetchOperations = async () => {
  loadingOps.value = true
  try {
    const card = defaultProcessCard()
    // Get operations for default +Z direction
    const res = await stlApi.convert(stlFile.value, card, '+Z')
    if (res.data.success) {
      operations.value = res.data.data.operations || []
    }
    // Also get direction plan
    fetchDirectionPlan(card)
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
      directionPlans.value = res.data.directions || {}
      recommendedOrder.value = res.data.recommended_order || Object.keys(res.data.directions || {})
      directionExplanation.value = res.data.explanation || ''
      directionSource.value = res.data.source || ''
      if (recommendedOrder.value.length > 0) {
        activeDirection.value = recommendedOrder.value[0]
      }
    }
  } catch (e) {
    console.error('方向规划失败:', e)
  }
}

const generateGcode = async () => {
  loadingGcode.value = true
  try {
    const card = defaultProcessCard()
    // Generate +Z G-code
    const res = await stlApi.generateGcode(stlFile.value, card, operations.value, '+Z')
    if (res.data.success) {
      gcode.value = res.data.data.gcode || ''
    }
    // Generate G-code for all needed directions
    await generateAllDirectionGcodes(card)
  } catch (e) {
    console.error('G代码生成失败:', e)
  } finally {
    loadingGcode.value = false
  }
}

const generateAllDirectionGcodes = async (card) => {
  for (const dir of recommendedOrder.value) {
    try {
      const dirRes = await stlApi.convert(stlFile.value, card, dir)
      if (dirRes.data.success) {
        const ops = dirRes.data.data.operations || []
        const gRes = await stlApi.generateGcode(stlFile.value, card, ops, dir)
        if (gRes.data.success) {
          directionGcodes.value[dir] = gRes.data.data.gcode || ''
        }
      }
    } catch (e) {
      console.error(`方向${dir} G代码生成失败:`, e)
    }
  }
}

const copyDirectionGcode = async (dir) => {
  const code = directionGcodes.value[dir]
  if (!code) return
  await navigator.clipboard.writeText(code)
  copiedDir.value = dir
  setTimeout(() => { copiedDir.value = '' }, 2000)
}

const validateDirectionOnline = (dir) => {
  const code = directionGcodes.value[dir]
  if (!code) return
  window.open(`https://ncviewer.com/?code=${encodeURIComponent(code)}`, '_blank')
}

const copyGcode = async () => {
  await navigator.clipboard.writeText(gcode.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

const validateOnline = () => {
  window.open(`https://ncviewer.com/?code=${encodeURIComponent(gcode.value)}`, '_blank')
}

const copyOperations = async () => {
  const header = '序号\t内容\t参数\t设备\t备注'
  const rows = operations.value.map(op =>
    `${op.sequence}\t${op.content}\t${op.parameters}\t${op.equipment}\t${op.remark || ''}`
  )
  await navigator.clipboard.writeText([header, ...rows].join('\n'))
  opsCopied.value = true
  setTimeout(() => { opsCopied.value = false }, 2000)
}

const downloadOperations = () => {
  const header = '序号,内容,参数,设备,备注'
  const rows = operations.value.map(op =>
    `"${op.sequence}","${op.content}","${op.parameters}","${op.equipment}","${op.remark || ''}"`
  )
  const csv = '\uFEFF' + [header, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `STL工序表_${stlFileName.value.replace(/\.\w+$/i, '')}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

const defaultProcessCard = () => ({
  product_name: stlFileName.value.replace(/\.stl$/i, ''),
  process_name: 'STL加工',
  process_number: '001',
  version: 'A',
  equipment: 'CNC加工中心',
  control_system: 'FANUC',
  fixture: '通用夹具',
  material: '铝合金',
  tool_info: { name: '立铣刀', length: 75, diameter: 10 }
})

onBeforeUnmount(() => {
  renderer?.dispose()
  controls?.dispose()
  cancelAnimationFrame(animFrameId)
  if (objectUrl) URL.revokeObjectURL(objectUrl)
})
</script>
