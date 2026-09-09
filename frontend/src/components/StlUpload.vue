<template>
  <div class="bg-white rounded-xl shadow-lg p-4 flex flex-col gap-4" style="min-height: calc(100vh - 160px)">
    <h2 class="text-xl font-bold text-gray-800 shrink-0">STL文件转换</h2>

    <div class="grid grid-cols-2 gap-4 shrink-0" style="height: 300px">
      <div class="border border-gray-400 rounded-xl overflow-hidden flex flex-col">
        <div class="px-4 py-2 bg-gray-50 border-b text-sm font-medium text-gray-700 shrink-0">上传STL文件</div>
        <div class="flex-1 flex flex-col items-center p-4 overflow-y-auto min-h-0">
          <div
            @click="triggerUpload"
            @dragover.prevent
            @drop.prevent="handleDrop"
            class="w-full shrink-0 border-2 border-dashed border-gray-500 rounded-lg px-4 py-3 text-center hover:border-blue-500 hover:bg-blue-50 cursor-pointer transition-all"
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
          <div class="mt-2 w-full flex gap-2">
            <button
              @click="generateAll"
              :disabled="!stlFile || !hasTool || loadingOps"
              class="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-sm"
            >
              {{ loadingOps ? '生成中...' : '生成工序与G代码（分方向）' }}
            </button>
            <button
              v-if="loadingOps"
              @click="cancelGenerate"
              class="px-3 py-2 border border-red-300 text-red-600 rounded-lg text-sm hover:bg-red-50"
            >停止</button>
          </div>
          <div v-if="directionProgress" class="mt-2 w-full text-sm text-blue-600">{{ directionProgress }}</div>
          <div v-if="directionExplanation" class="mt-1 w-full text-xs text-gray-500">六方向分析（{{ directionSource === 'ai' ? 'AI推荐' : '本地规则' }}）：{{ directionExplanation }}</div>
        </div>
      </div>

      <div class="border border-gray-400 rounded-xl overflow-hidden flex flex-col">
        <div class="px-4 py-2 bg-gray-50 border-b text-sm font-medium text-gray-700 shrink-0">模型预览</div>
        <div ref="stlContainer" class="flex-1 relative bg-gray-100">
          <canvas ref="stlCanvas" class="w-full h-full block"></canvas>
          <div v-if="!stlFileName" class="absolute inset-0 flex items-center justify-center text-sm text-gray-400">上传STL文件后显示模型</div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4 shrink-0" style="height: 380px">
      <div class="border border-gray-400 rounded-xl overflow-hidden flex flex-col">
        <div class="px-4 py-2 bg-gray-50 border-b flex items-center justify-between shrink-0">
          <span class="text-sm font-medium text-gray-700">加工工序（按方向编排，{{ totalOpCount }} 条）</span>
          <div class="flex gap-2">
            <button v-if="totalOpCount" @click="copyOperations" class="px-2 py-1 bg-gray-200 text-gray-600 text-xs rounded">{{ opsCopied ? '已复制' : '复制' }}</button>
            <button v-if="totalOpCount" @click="downloadOperations" class="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">下载CSV</button>
          </div>
        </div>
        <div class="flex-1 overflow-auto">
          <div v-if="!totalOpCount" class="flex items-center justify-center h-full text-sm text-gray-400">上传文件后生成分方向工序</div>
          <table v-else class="w-full text-xs border-collapse">
            <thead class="bg-gray-50 sticky top-0">
              <tr>
                <th class="border border-gray-300 px-2 py-1 text-left w-14">方向</th>
                <th class="border border-gray-300 px-2 py-1 text-left w-10">序号</th>
                <th class="border border-gray-300 px-2 py-1 text-left">内容</th>
                <th class="border border-gray-300 px-2 py-1 text-left">参数</th>
                <th class="border border-gray-300 px-2 py-1 text-left">设备</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="(row, index) in masterRows" :key="index">
                <tr v-if="row.type === 'header'" class="bg-blue-50">
                  <td colspan="5" class="border border-gray-300 px-2 py-1.5 font-medium text-blue-800">
                    🔄 翻面装夹：{{ directionLabels[row.dir] || row.dir }}（{{ row.dir }}）
                  </td>
                </tr>
                <tr v-else class="hover:bg-gray-50">
                  <td class="border border-gray-300 px-2 py-1">
                    <span class="px-1.5 py-0.5 bg-indigo-100 text-indigo-700 rounded text-[10px]">{{ directionLabels[row.dir] || row.dir }}</span>
                  </td>
                  <td class="border border-gray-300 px-2 py-1">{{ row.sequence }}</td>
                  <td class="border border-gray-300 px-2 py-1">{{ row.content }}</td>
                  <td class="border border-gray-300 px-2 py-1 font-mono">{{ row.parameters }}</td>
                  <td class="border border-gray-300 px-2 py-1">{{ row.equipment }}</td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>

      <div class="border border-gray-400 rounded-xl overflow-hidden flex flex-col">
        <div class="px-4 py-2 bg-gray-50 border-b shrink-0">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-gray-700">G代码校验状态</span>
            <button
              v-if="directionGcodes[activeDirection] && directionValidations[activeDirection]?.valid"
              @click="copyDirectionGcode(activeDirection)"
              class="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded-lg"
            >{{ copiedDir === activeDirection ? '已复制!' : '复制待审核代码' }}</button>
          </div>
          <div class="flex border-t bg-gray-50 pt-1 overflow-x-auto">
            <button
              v-for="dir in recommendedOrder"
              :key="dir"
              @click="activeDirection = dir"
              :class="[
                'px-3 py-1.5 text-xs whitespace-nowrap border-r border-gray-200 first:border-l-0',
                activeDirection === dir
                  ? 'bg-white text-blue-700 font-medium border-b-2 border-b-blue-500'
                  : 'text-gray-600 hover:text-blue-600',
                directionGcodes[dir] ? '' : 'opacity-50'
              ]"
            >
              {{ directionLabels[dir] || dir }} ({{ dir }})
              <span v-if="directionGcodes[dir]" class="text-gray-400">·{{ directionGcodes[dir].split('\n').length }}行</span>
            </button>
          </div>
        </div>
        <div
          v-if="directionValidations[activeDirection]?.errors?.length"
          class="px-3 py-2 bg-red-50 border-b text-xs text-red-700 shrink-0"
        >
          <p v-for="error in directionValidations[activeDirection].errors" :key="`${error.line}-${error.code}`">
            第{{ error.line }}行 {{ error.code }}：{{ error.message }}
          </p>
        </div>
        <div
          v-if="directionValidations[activeDirection]?.warnings?.length"
          class="px-3 py-2 bg-yellow-50 border-b text-xs text-yellow-800 shrink-0"
        >
          <p v-for="warning in directionValidations[activeDirection].warnings" :key="`${warning.line}-${warning.message}`">
            第{{ warning.line }}行：{{ warning.message }}
          </p>
        </div>
        <div class="flex-1 flex flex-col items-center justify-center bg-gray-50 p-4 text-center gap-2 overflow-auto">
          <div v-if="!directionGcodes[activeDirection]" class="text-sm text-gray-400">
            {{ loadingOps ? '正在生成，请稍候…' : '该方向尚未生成' }}
          </div>
          <template v-else>
            <p class="text-sm text-gray-700">当前方向 {{ directionLabels[activeDirection] || activeDirection }} 共
              <span class="font-bold text-gray-900">{{ directionGcodes[activeDirection].split('\n').length }}</span> 行
            </p>
            <p
              v-if="directionValidations[activeDirection]?.valid"
              class="text-sm font-medium text-green-700"
            >✓ 安全验证通过，可复制待审核</p>
            <button
              v-if="directionGcodes[activeDirection] && directionValidations[activeDirection]?.valid"
              @click="copyDirectionGcode(activeDirection)"
              class="px-4 py-2 bg-gray-700 text-white text-sm rounded-lg hover:bg-gray-800"
            >{{ copiedDir === activeDirection ? '已复制!' : '复制待审核代码' }}</button>
            <p class="text-xs text-gray-400">完整代码见下方"完整G代码"窗口</p>
          </template>
        </div>
      </div>
    </div>

    <div class="border border-gray-400 rounded-xl overflow-hidden flex flex-col shrink-0" style="height: 440px">
      <div class="px-4 py-2 bg-gray-50 border-b shrink-0">
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium text-gray-700">完整G代码（{{ directionLabels[activeDirection] || activeDirection }} · {{ directionGcodes[activeDirection] ? directionGcodes[activeDirection].split('\n').length : 0 }} 行）</span>
          <span class="text-xs text-gray-500">按方向分份 · 加工顺序为工序表中的翻面装夹顺序</span>
        </div>
        <div class="flex border-t bg-gray-50 pt-1 overflow-x-auto">
          <button
            v-for="dir in recommendedOrder"
            :key="dir"
            @click="activeDirection = dir"
            :class="[
              'px-3 py-1.5 text-xs whitespace-nowrap border-r border-gray-300 first:border-l-0',
              activeDirection === dir
                ? 'bg-white text-blue-700 font-medium border-b-2 border-b-blue-500'
                : 'text-gray-600 hover:text-blue-600',
              directionGcodes[dir] ? '' : 'opacity-50'
            ]"
          >
            {{ directionLabels[dir] || dir }} ({{ dir }})
            <span v-if="directionGcodes[dir]" class="text-gray-400">·{{ directionGcodes[dir].split('\n').length }}行</span>
          </button>
        </div>
      </div>
      <div class="flex-1 overflow-auto bg-gray-50 p-3">
        <div v-if="!directionGcodes[activeDirection]" class="flex flex-col items-center justify-center h-full text-sm text-gray-400 gap-1">
          <span>{{ loadingOps ? '正在生成，请稍候…' : '点击上方"生成工序与G代码（分方向）"生成完整代码' }}</span>
          <span v-if="!loadingOps" class="text-xs text-gray-300">本窗口只显示代码；安全验证结果在右上"G代码"状态卡中</span>
        </div>
        <pre v-else class="text-xs font-mono text-gray-800 whitespace-pre-wrap">{{ directionGcodes[activeDirection] }}</pre>
      </div>
    </div>

    <!-- 刀路路线图：范围切换 + 自动渲染大窗 -->
    <div class="mt-4 flex items-center justify-between gap-3 flex-wrap shrink-0">
      <div class="flex items-center gap-2 flex-wrap">
        <span class="text-sm font-medium text-gray-700">路线图范围：</span>
        <button
          @click="routeMode = 'all'"
          :class="[
            'px-3 py-1.5 text-xs rounded-lg border transition-colors',
            routeMode === 'all'
              ? 'bg-blue-600 text-white border-blue-600'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-blue-50'
          ]"
        >
          全部方向合并<span v-if="generatedDirCount">（{{ generatedDirCount }} 个方向）</span>
        </button>
        <button
          @click="routeMode = 'single'"
          :disabled="!directionGcodes[activeDirection]"
          :class="[
            'px-3 py-1.5 text-xs rounded-lg border transition-colors',
            routeMode === 'single'
              ? 'bg-blue-600 text-white border-blue-600'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-blue-50',
            !directionGcodes[activeDirection] ? 'opacity-50 cursor-not-allowed' : ''
          ]"
        >
          当前方向（{{ directionLabels[activeDirection] || activeDirection }}）
        </button>
      </div>
      <span class="text-xs text-yellow-700">全方向合并为多面加工叠加示意，不代表真实翻面装夹运动轨迹；正式核验请逐方向查看。</span>
    </div>
    <ToolpathRouteMap
      :gcode="routeGcode"
      :validation="routeValidation"
      title="刀路路线图"
      subtitle="路线图仅用于辅助检查 · 正式上机前仍需人工审核、空运行和试切"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import * as THREE from 'three'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { stlApi } from '../api'
import ToolpathRouteMap from './ToolpathRouteMap.vue'

const fileInput = ref(null)
const stlFileName = ref('')
const stlFile = ref('')
const loadingOps = ref(false)
const directionProgress = ref('')
const copiedDir = ref('')
const opsCopied = ref(false)
const stlCanvas = ref(null)
const stlContainer = ref(null)
const tool = ref({ name: '立铣刀（仿真）', length: 75, diameter: null })
const directionValidations = ref({})
const directionGcodes = ref({})
const operationsByDirection = ref({})
const recommendedOrder = ref([])
const activeDirection = ref('+Z')
const routeMode = ref('all') // 'all' | 'single'：路线图范围
const directionExplanation = ref('')
const directionSource = ref('')
const directionLabels = { '+Z': '顶面', '-Z': '底面', '+X': '右面', '-X': '左面', '+Y': '前面', '-Y': '后面' }
const hasTool = computed(() => Number.isFinite(Number(tool.value.diameter)) && Number(tool.value.diameter) > 0)

let renderer = null
let animFrameId = null
let objectUrl = null
let controls = null
let cancelled = false

const triggerUpload = () => fileInput.value?.click()
const handleFileSelect = (e) => processFile(e.target.files?.[0])
const handleDrop = (e) => processFile(e.dataTransfer?.files?.[0])

const processFile = async (file) => {
  if (!file || !file.name.toLowerCase().endsWith('.stl')) return
  stlFileName.value = file.name
  operationsByDirection.value = {}
  directionGcodes.value = {}
  directionValidations.value = {}
  recommendedOrder.value = []
  activeDirection.value = '+Z'
  directionExplanation.value = ''
  directionSource.value = ''
  directionProgress.value = ''

  const reader = new FileReader()
  reader.onload = async (e) => {
    stlFile.value = e.target.result.split(',')[1] || ''
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

const generateAll = async () => {
  if (!hasTool.value || loadingOps.value) return
  loadingOps.value = true
  cancelled = false
  operationsByDirection.value = {}
  directionGcodes.value = {}
  directionValidations.value = {}
  try {
    const card = defaultProcessCard()

    // 1) 六方向分析：以 AI/规则推荐确定加工顺序（工序的基准骨架）
    directionProgress.value = '正在分析六个方向的加工特征与推荐顺序…'
    const plan = await stlApi.planDirections(stlFile.value, card)
    const order = plan.data?.recommended_order || []
    if (!order.length) {
      alert('未能分析出需要加工的方向')
      return
    }
    recommendedOrder.value = order
    activeDirection.value = order[0]
    directionExplanation.value = plan.data?.explanation || ''
    directionSource.value = plan.data?.source || ''

    // 2) 按顺序逐方向生成该方向的工序，并随即生成该方向 G 代码（工序是基准）
    for (let index = 0; index < order.length; index++) {
      if (cancelled) break
      const dir = order[index]
      const label = directionLabels[dir] || dir
      directionProgress.value = `正在生成 ${label}(${dir}) 工序（${index + 1}/${order.length}）…`
      const res = await stlApi.convert(stlFile.value, card, dir)
      if (!res.data?.success) continue
      const ops = res.data.data.operations || []
      operationsByDirection.value[dir] = ops

      directionProgress.value = `正在生成 ${label}(${dir}) 的 G 代码（${index + 1}/${order.length}）…`
      const gRes = await stlApi.generateGcode(stlFile.value, card, ops, dir)
      if (gRes.data?.success) {
        directionGcodes.value[dir] = gRes.data.data.gcode || ''
        directionValidations.value[dir] = gRes.data.data.validation || { valid: false, errors: [], warnings: [] }
      }
    }
    if (cancelled) {
      directionProgress.value = '已停止（已生成的部分保留）'
    } else {
      directionProgress.value = '完成：全部方向工序与 G 代码已生成'
    }
  } catch (e) {
    console.error('分方向生成失败:', e)
    alert(`生成失败: ${e.response?.data?.detail || e.message}`)
    directionProgress.value = ''
  } finally {
    loadingOps.value = false
  }
}

const cancelGenerate = () => {
  cancelled = true
}

// 主工序表：按推荐顺序把各方向工序拼成一张带方向标注的大表
const masterRows = computed(() => {
  const rows = []
  for (const dir of recommendedOrder.value) {
    const ops = operationsByDirection.value[dir] || []
    if (!ops.length) continue
    rows.push({ type: 'header', dir })
    ops.forEach((op) => rows.push({ type: 'op', dir, ...op }))
  }
  return rows
})
const totalOpCount = computed(() => masterRows.value.filter((row) => row.type === 'op').length)
const generatedDirCount = computed(() => recommendedOrder.value.filter((dir) => directionGcodes.value[dir]).length)

// 底部路线图数据：默认全方向合并，也可切换为只显示当前方向
const routeGcode = computed(() => {
  if (routeMode.value === 'single') return directionGcodes.value[activeDirection.value] || ''
  const parts = []
  for (const dir of recommendedOrder.value) {
    const g = directionGcodes.value[dir]
    if (!g) continue
    parts.push(`; ============ 翻面装夹 ${directionLabels[dir] || dir} (${dir}) ============`)
    parts.push(g.trim())
  }
  return parts.join('\n')
})
const routeValidation = computed(() => {
  if (routeMode.value === 'all') {
    // 合并视图为多方向叠加示意，仅提示、不阻断渲染
    return {
      valid: true,
      errors: [],
      warnings: [{
        line: 0,
        code: 'MERGED',
        message: '多方向合并展示为叠加示意，不代表真实翻面装夹运动轨迹，正式核验请逐方向查看。'
      }]
    }
  }
  return directionValidations.value[activeDirection.value] || { valid: false, errors: [], warnings: [] }
})

const copyDirectionGcode = async (dir) => {
  if (!directionValidations.value[dir]?.valid || !directionGcodes.value[dir]) return
  await navigator.clipboard.writeText(directionGcodes.value[dir])
  copiedDir.value = dir
  setTimeout(() => { copiedDir.value = '' }, 2000)
}

const copyOperations = async () => {
  const header = '方向\t序号\t内容\t参数\t设备\t备注'
  const rows = masterRows.value.filter((row) => row.type === 'op')
    .map((op) => `${directionLabels[op.dir] || op.dir}\t${op.sequence}\t${op.content}\t${op.parameters}\t${op.equipment}\t${op.remark || ''}`)
  await navigator.clipboard.writeText([header, ...rows].join('\n'))
  opsCopied.value = true
  setTimeout(() => { opsCopied.value = false }, 2000)
}

const downloadOperations = () => {
  const header = '方向,序号,内容,参数,设备,备注'
  const rows = masterRows.value.filter((row) => row.type === 'op')
    .map((op) => `"${directionLabels[op.dir] || op.dir}","${op.sequence}","${op.content}","${op.parameters}","${op.equipment}","${op.remark || ''}"`)
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
