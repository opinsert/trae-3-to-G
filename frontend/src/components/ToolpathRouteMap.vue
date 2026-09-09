<template>
  <section class="mt-8 bg-white rounded-xl shadow-lg overflow-hidden flex flex-col" style="height: 72vh; min-height: 480px;">
    <div class="px-4 py-3 border-b bg-indigo-50 flex items-center justify-between gap-3 flex-wrap shrink-0">
      <div class="flex items-center gap-3 flex-wrap">
        <h2 v-if="title" class="text-lg font-bold text-indigo-800">{{ title }}</h2>
        <span :class="[
          'px-3 py-1 rounded-full text-xs font-medium',
          badgeClass
        ]">
          {{ badgeText }}
        </span>
      </div>
      <div v-if="canView" class="flex items-center gap-1 flex-wrap">
        <button
          v-for="v in headerViews"
          :key="v.key"
          @click="setView(v.key)"
          :class="[
            'px-3 py-1.5 rounded-lg text-sm transition-colors',
            activeView === v.key
              ? 'bg-indigo-600 text-white'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-indigo-50'
          ]"
        >
          {{ v.label }}
        </button>
      </div>
    </div>

    <div ref="containerRef" class="relative flex-1 min-h-0 bg-slate-900">
      <canvas ref="canvasRef" class="block w-full h-full"></canvas>

      <!-- 左上角方向指示立方体 -->
      <canvas
        ref="gizmoCanvasRef"
        v-show="rendered"
        class="absolute left-2 top-2 w-[90px] h-[90px] z-10 cursor-grab select-none touch-none"
        @pointerdown="onGizmoPointerDown"
        @pointermove="onGizmoPointerMove"
        @pointerup="onGizmoPointerUp"
        @pointercancel="onGizmoPointerUp"
      ></canvas>

      <!-- 覆盖提示层 -->
      <div
        v-if="!error && !rendered && props.gcode && !validation.valid"
        class="absolute inset-0 flex items-center justify-center bg-slate-900 bg-opacity-80 px-6 text-center"
      >
        <div>
          <p class="text-sm text-red-300">G代码未通过安全验证，已阻止路线图渲染。</p>
          <p class="mt-1 text-xs text-slate-400">修正代码并重新验证通过后，将自动在此出图。</p>
        </div>
      </div>
      <div
        v-else-if="!error && !rendered && props.gcode && rendering"
        class="absolute inset-0 flex items-center justify-center bg-slate-900 bg-opacity-80 px-6 text-center"
      >
        <p class="text-sm text-slate-300">正在解析并渲染刀路…</p>
      </div>
      <div
        v-else-if="!error && !rendered && !props.gcode"
        class="absolute inset-0 flex items-center justify-center bg-slate-900 px-6 text-center"
      >
        <div>
          <p class="text-sm text-slate-300">暂无 G 代码</p>
          <p class="mt-1 text-xs text-slate-500">生成并验证通过后，将自动在此渲染 3D 刀路路线图。</p>
        </div>
      </div>
      <div
        v-else-if="error"
        class="absolute inset-0 flex items-center justify-center bg-slate-900 bg-opacity-85 px-6 text-center"
      >
        <p class="text-sm text-red-400">路线图渲染失败：{{ error }}</p>
      </div>

      <!-- 已渲染时的操作提示 -->
      <div
        v-if="rendered"
        class="absolute left-3 bottom-3 right-3 flex items-center justify-between gap-3 pointer-events-none"
      >
        <span class="text-[11px] text-slate-400">{{ props.subtitle }}</span>
        <span class="text-[11px] text-slate-500 font-mono">{{ lineCount }} 行</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { LineSegments2 } from 'three/examples/jsm/lines/LineSegments2.js'
import { LineSegmentsGeometry } from 'three/examples/jsm/lines/LineSegmentsGeometry.js'
import { LineMaterial } from 'three/examples/jsm/lines/LineMaterial.js'

const props = defineProps({
  gcode: { type: String, default: '' },
  validation: {
    type: Object,
    default: () => ({ valid: false, errors: [], warnings: [] })
  },
  title: { type: String, default: '刀路路线图' },
  subtitle: { type: String, default: '可拖拽旋转 · 滚轮缩放 · 右键平移' }
})

const containerRef = ref(null)
const canvasRef = ref(null)
const gizmoCanvasRef = ref(null)
const error = ref('')
const rendering = ref(false)
const rendered = ref(false)
const activeView = ref('iso')

// dir：观察者相对包围盒中心的方向；up：相机上向量（避免视轴与 up 平行取景失效）
// 约定：+Y=前 / -Y=后 / +X=右 / -X=左 / +Z=上 / -Z=下
const VIEWS = {
  iso: { label: '轴侧', dir: [-0.16, 0.65, 0.74], up: [0, 1, 0] },
  top: { label: '俯视', dir: [0, 0, 1], up: [0, 1, 0] },
  front: { label: '前视', dir: [0, 1, 0], up: [0, 0, 1] },
  left: { label: '左视', dir: [-1, 0, 0], up: [0, 1, 0] },
  right: { label: '右视', dir: [1, 0, 0], up: [0, 1, 0] },
  back: { label: '后视', dir: [0, -1, 0], up: [0, 0, 1] },
  bottom: { label: '仰视', dir: [0, 0, -1], up: [0, 1, 0] }
}
// 顶部工具条展示的视角按钮
const headerViews = ['iso', 'top', 'front', 'left'].map((key) => ({ key, ...VIEWS[key] }))
// 点击方向盒某个面时的法向 → 视角 key
const FACE_VIEW_MAP = {
  '+Y': 'front', '-Y': 'back', '+X': 'right', '-X': 'left', '+Z': 'top', '-Z': 'bottom'
}

let renderer = null
let scene = null
let camera = null
let controls = null
let gizmoRenderer = null
let gizmoScene = null
let gizmoCamera = null
let gizmoCube = null
let gizmoHitBox = null
let rafId = 0
let resizeObserver = null
let lastBounds = null

// 当前场景中可替换的对象（每次重建前清理）
let cutObject = null
let travelObject = null
let decoGroup = null
let disposables = []

const lineCount = computed(() => (props.gcode ? props.gcode.split('\n').length : 0))
const canView = computed(() => rendered.value)

const badgeText = computed(() => {
  if (!props.gcode) return '待生成'
  if (!props.validation.valid) return '验证失败'
  return '规则验证通过'
})
const badgeClass = computed(() => {
  if (!props.gcode) return 'bg-gray-100 text-gray-500'
  if (!props.validation.valid) return 'bg-red-100 text-red-700'
  return 'bg-green-100 text-green-700'
})

const TAU = Math.PI * 2

// ---------- G 代码解析：产出线段 + 包围盒 ----------
function parseToolpath(gcode) {
  const cutPositions = []
  const travelPositions = []
  const min = { x: Infinity, y: Infinity, z: Infinity }
  const max = { x: -Infinity, y: -Infinity, z: -Infinity }
  let cur = { x: 0, y: 0, z: 0 }
  let absolute = true
  let unit = 1 // 1=mm；G20 英寸时切 25.4
  let modal = 0 // 模态运动代码

  const mark = (p) => {
    for (const a of ['x', 'y', 'z']) {
      if (p[a] < min[a]) min[a] = p[a]
      if (p[a] > max[a]) max[a] = p[a]
    }
  }

  const readAxis = (line, axis) => {
    const m = line.match(new RegExp(`(?:^|[^A-Za-z])${axis}(-?\\d+(?:\\.\\d+)?)`, 'i'))
    return m ? parseFloat(m[1]) * unit : null
  }

  // 圆弧：IJ 相对圆心 或 R 半径，细分采样为短直线段
  const addArc = (start, end, i, j, r, cw, isCut, scale) => {
    let cx, cy
    // 先用 IJ 分支填 cx/cy
    if (i !== null && j !== null) {
      cx = start.x + i
      cy = start.y + j
    } else if (r !== null && r !== 0) {
      const dx = end.x - start.x
      const dy = end.y - start.y
      const chord = Math.hypot(dx, dy)
      const rr = Math.abs(r)
      const h = Math.sqrt(Math.max(rr * rr - (chord / 2) * (chord / 2), 0))
      const mx = (start.x + end.x) / 2
      const my = (start.y + end.y) / 2
      // 垂直于弦的两个候选圆心
      const px = -dy / (chord || 1)
      const py = dx / (chord || 1)
      const c1 = { x: mx + px * h, y: my + py * h }
      const c2 = { x: mx - px * h, y: my - py * h }
      const pick = (c) => {
        const a0 = Math.atan2(start.y - c.y, start.x - c.x)
        const a1 = Math.atan2(end.y - c.y, end.x - c.x)
        let sw = a1 - a0
        if (cw) { if (sw > 0) sw -= TAU } else { if (sw < 0) sw += TAU }
        return Math.abs(sw)
      }
      cx = pick(c1) <= pick(c2) ? c1.x : c2.x
      cy = pick(c1) <= pick(c2) ? c1.y : c2.y
    } else {
      return
    }
    const radius = Math.hypot(start.x - cx, start.y - cy)
    if (radius < 1e-6) return
    const a0 = Math.atan2(start.y - cy, start.x - cx)
    const a1 = Math.atan2(end.y - cy, end.x - cx)
    let sweep = a1 - a0
    if (cw) { if (sweep > 0) sweep -= TAU } else { if (sweep < 0) sweep += TAU }
    const steps = Math.max(2, Math.ceil(Math.abs(sweep) * radius / (0.8 * scale)))
    const arr = isCut ? cutPositions : travelPositions
    let prev = start
    for (let k = 1; k <= steps; k++) {
      const ang = a0 + sweep * (k / steps)
      const p = { x: cx + Math.cos(ang) * radius, y: cy + Math.sin(ang) * radius, z: start.z }
      arr.push(prev.x, prev.y, prev.z, p.x, p.y, p.z)
      mark(p)
      prev = p
    }
    return { x: end.x, y: end.y, z: start.z }
  }

  for (const rawLine of gcode.split(/\r?\n/)) {
    const line = rawLine.replace(/\([^)]*\)/g, ' ').replace(/;[^\r\n]*/g, ' ')
    if (!line.trim()) continue
    if (/\bG91\b/i.test(line)) absolute = false
    if (/\bG90\b/i.test(line)) absolute = true
    if (/\bG20\b/i.test(line)) unit = 25.4
    if (/\bG21\b/i.test(line)) unit = 1

    // 显式运动代码（G0/G1/G2/G3）
    let motion = null
    for (const m of line.matchAll(/\bG(\d+(?:\.\d+)?)\b/g)) {
      const v = parseInt(m[1], 10)
      if (v >= 0 && v <= 3) motion = v
    }
    const axisPresent = /(?:^|[^A-Za-z])(?:X|Y|Z)(-?[\d.]+)/i.test(line)
    const cmd = motion !== null ? motion : (axisPresent ? modal : null)
    if (cmd === null) continue
    modal = cmd

    // 终点坐标（缺省保持当前值）
    const end = { x: cur.x, y: cur.y, z: cur.z }
    for (const a of ['x', 'y', 'z']) {
      const v = readAxis(line, a)
      if (v === null) continue
      end[a] = absolute ? v : cur[a] + v
    }

    if (cmd === 2 || cmd === 3) {
      const iRaw = line.match(/(?:^|[^A-Za-z])I(-?\d+(?:\.\d+)?)/i)
      const jRaw = line.match(/(?:^|[^A-Za-z])J(-?\d+(?:\.\d+)?)/i)
      const rRaw = line.match(/(?:^|[^A-Za-z])R(-?\d+(?:\.\d+)?)/i)
      const i = iRaw ? parseFloat(iRaw[1]) * unit : null
      const j = jRaw ? parseFloat(jRaw[1]) * unit : null
      const r = rRaw ? parseFloat(rRaw[1]) * unit : null
      if (i !== null || j !== null || r !== null) {
        addArc(cur, end, i, j, r, cmd === 2, true, unit)
      } else {
        // 无中心信息：退化为直线
        cutPositions.push(cur.x, cur.y, cur.z, end.x, end.y, end.z)
      }
      mark(end)
      cur = end
      continue
    }

    const same = cur.x === end.x && cur.y === end.y && cur.z === end.z
    if (!same) {
      if (cmd === 0) travelPositions.push(cur.x, cur.y, cur.z, end.x, end.y, end.z)
      else cutPositions.push(cur.x, cur.y, cur.z, end.x, end.y, end.z)
    }
    mark(end)
    cur = end
  }

  const hasMove = min.x !== Infinity || min.y !== Infinity || min.z !== Infinity
  if (!hasMove) return null
  for (const a of ['x', 'y', 'z']) {
    if (min[a] === Infinity) { min[a] = 0; max[a] = 0 }
  }
  return { cutPositions, travelPositions, min, max }
}

// ---------- 场景对象 ----------
function disposeObject(obj) {
  if (!obj) return
  scene?.remove(obj)
  obj.traverse((child) => {
    if (child.geometry) child.geometry.dispose()
    if (child.material) {
      if (Array.isArray(child.material)) child.material.forEach((m) => m.dispose())
      else child.material.dispose()
    }
  })
}

function buildLines(positions, color, linewidth, opacity) {
  const geometry = new LineSegmentsGeometry()
  geometry.setPositions(positions)
  const material = new LineMaterial({
    color,
    linewidth,
    transparent: opacity !== undefined,
    opacity: opacity !== undefined ? opacity : 1
  })
  const w = renderer.domElement.clientWidth || 1
  const h = renderer.domElement.clientHeight || 1
  material.resolution.set(w, h)
  return new LineSegments2(geometry, material)
}

function clearPathObjects() {
  disposeObject(cutObject)
  disposeObject(travelObject)
  disposeObject(decoGroup)
  cutObject = null
  travelObject = null
  decoGroup = null
  disposables = []
}

function buildDeco(bounds) {
  const g = new THREE.Group()
  const span = Math.max(
    bounds.max.x - bounds.min.x,
    bounds.max.y - bounds.min.y,
    bounds.max.z - bounds.min.z,
    1
  )
  const cx = (bounds.min.x + bounds.max.x) / 2
  const cy = (bounds.min.y + bounds.max.y) / 2
  const z0 = bounds.min.z

  // 红色半透明基准平面（底面 z=min）
  const w = Math.max(bounds.max.x - bounds.min.x, 1) * 1.5
  const hgt = Math.max(bounds.max.y - bounds.min.y, 1) * 1.5
  const planeGeo = new THREE.PlaneGeometry(w, hgt)
  const planeMat = new THREE.MeshBasicMaterial({
    color: 0xff3b30,
    transparent: true,
    opacity: 0.32,
    side: THREE.DoubleSide,
    depthWrite: false
  })
  const plane = new THREE.Mesh(planeGeo, planeMat)
  plane.position.set(cx, cy, z0)
  g.add(plane)

  // 平面外框线
  const boxGeo = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(cx - w / 2, cy - hgt / 2, z0),
    new THREE.Vector3(cx + w / 2, cy - hgt / 2, z0),
    new THREE.Vector3(cx + w / 2, cy + hgt / 2, z0),
    new THREE.Vector3(cx - w / 2, cy + hgt / 2, z0),
    new THREE.Vector3(cx - w / 2, cy - hgt / 2, z0)
  ])
  const frame = new THREE.Line(boxGeo, new THREE.LineBasicMaterial({ color: 0xff8a85 }))
  g.add(frame)

  // 坐标轴（红 X / 绿 Y / 蓝 Z），锚在平面左下角
  const axes = new THREE.AxesHelper(Math.min(span * 0.9, Math.max(w, hgt) * 0.5))
  axes.position.set(bounds.min.x, bounds.min.y, z0)
  g.add(axes)

  scene.add(g)
  decoGroup = g
}

function fitCamera() {
  if (!camera || !lastBounds) return
  const b = lastBounds
  const size = {
    x: Math.max(b.max.x - b.min.x, 0.001),
    y: Math.max(b.max.y - b.min.y, 0.001),
    z: Math.max(b.max.z - b.min.z, 0.001)
  }
  const maxDim = Math.max(size.x, size.y, size.z, 1)
  const center = {
    x: (b.min.x + b.max.x) / 2,
    y: (b.min.y + b.max.y) / 2,
    z: (b.min.z + b.max.z) / 2
  }
  const mode = VIEWS[activeView.value] || VIEWS.iso
  const radius = maxDim * 2.2 + 10
  const norm = Math.hypot(mode.dir[0], mode.dir[1], mode.dir[2]) || 1

  camera.near = Math.max(radius / 1000, 0.05)
  camera.far = radius + maxDim * 8 + 500
  camera.up.set(mode.up[0], mode.up[1], mode.up[2])
  camera.position.set(
    center.x + (mode.dir[0] / norm) * radius,
    center.y + (mode.dir[1] / norm) * radius,
    center.z + (mode.dir[2] / norm) * radius
  )
  controls.target.set(center.x, center.y, center.z)
  camera.lookAt(center.x, center.y, center.z)
  controls.update()
  camera.updateProjectionMatrix()
}

function renderPath() {
  if (!scene) return
  error.value = ''
  rendered.value = false
  lastBounds = null

  const code = props.gcode
  if (!code) return
  if (!props.validation.valid) return

  let parsed
  try {
    parsed = parseToolpath(code)
  } catch (e) {
    console.error('刀路解析失败:', e)
    error.value = e?.message || '解析失败'
    return
  }
  if (!parsed) {
    error.value = '未检测到可渲染的运动指令（缺少 G0/G1/G2/G3 坐标行）。'
    return
  }

  rendering.value = true
  try {
    clearPathObjects()
    lastBounds = { min: parsed.min, max: parsed.max }

    if (parsed.cutPositions.length >= 6) {
      cutObject = buildLines(parsed.cutPositions, 0xffffff, 2.4, undefined)
      scene.add(cutObject)
    }
    if (parsed.travelPositions.length >= 6) {
      travelObject = buildLines(parsed.travelPositions, 0x94a3b8, 1, 0.75)
      scene.add(travelObject)
    }

    buildDeco(lastBounds)
    fitCamera()
    drawOnce()
    rendered.value = true
  } catch (e) {
    console.error('刀路路线图渲染失败:', e)
    error.value = e?.message || '未知错误'
  } finally {
    rendering.value = false
  }
}

const setView = (key) => {
  activeView.value = key
  if (rendered.value && lastBounds) {
    fitCamera()
    drawOnce()
  }
}

// 同步渲染一帧（headless / 首帧不依赖 rAF 也能出图；真实浏览器中动画循环持续运行）
function drawOnce() {
  if (!renderer || !scene || !camera) return
  controls.update()
  renderer.render(scene, camera)
  if (gizmoRenderer && gizmoScene) {
    syncGizmoCamera()
    gizmoRenderer.render(gizmoScene, gizmoCamera)
  }
}

function resize() {
  if (!renderer || !containerRef.value) return
  const w = containerRef.value.clientWidth || 1
  const h = containerRef.value.clientHeight || 1
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(w, h, false)
  if (cutObject) cutObject.material.resolution.set(w, h)
  if (travelObject) travelObject.material.resolution.set(w, h)
}

function buildGizmo() {
  const canvas = gizmoCanvasRef.value
  if (!canvas) return
  gizmoRenderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, preserveDrawingBuffer: true })
  gizmoRenderer.setClearColor(0x000000, 0)
  gizmoRenderer.setPixelRatio(window.devicePixelRatio)
  gizmoRenderer.setSize(90, 90, false)

  gizmoScene = new THREE.Scene()
  gizmoCamera = new THREE.PerspectiveCamera(35, 1, 0.1, 20)
  gizmoCamera.position.set(1.6, 1.4, 1.6)
  gizmoCamera.lookAt(0, 0, 0)

  gizmoCube = new THREE.Group()

  // 六个面：中心位置（相对立方体 ±0.5）、朝外目标、标签文字
  // 约定：+Y=前 / -Y=后 / +X=右 / -X=左 / +Z=上 / -Z=下
  const faces = [
    { label: '前', pos: [0, 0.5, 0], target: [0, 1, 0], up: [0, 0, 1] },
    { label: '后', pos: [0, -0.5, 0], target: [0, -1, 0], up: [0, 0, 1] },
    { label: '右', pos: [0.5, 0, 0], target: [1, 0, 0], up: [0, 0, 1] },
    { label: '左', pos: [-0.5, 0, 0], target: [-1, 0, 0], up: [0, 0, 1] },
    { label: '上', pos: [0, 0, 0.5], target: [0, 0, 1], up: [0, 1, 0] },
    { label: '下', pos: [0, 0, -0.5], target: [0, 0, -1], up: [0, 1, 0] }
  ]

  faces.forEach((f) => {
    const cv = document.createElement('canvas')
    cv.width = 128
    cv.height = 128
    const ctx = cv.getContext('2d')
    // 面板底色 + 描边（近深色卡片，白字）
    ctx.fillStyle = 'rgba(15,23,42,0.95)'
    ctx.fillRect(0, 0, 128, 128)
    ctx.strokeStyle = '#475569'
    ctx.lineWidth = 5
    ctx.strokeRect(2.5, 2.5, 123, 123)
    ctx.fillStyle = '#f8fafc'
    ctx.font = '40px "Microsoft YaHei", "PingFang SC", sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(f.label, 64, 66)

    const tex = new THREE.CanvasTexture(cv)
    tex.colorSpace = THREE.SRGBColorSpace
    const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: true })
    const plane = new THREE.Mesh(new THREE.PlaneGeometry(0.98, 0.98), mat)
    plane.position.set(f.pos[0], f.pos[1], f.pos[2])
    plane.up.set(f.up[0], f.up[1], f.up[2])
    plane.lookAt(f.target[0], f.target[1], f.target[2])
    gizmoCube.add(plane)
  })

  gizmoScene.add(gizmoCube)

  // 不可见的命中盒：用于点击面判定（与标签立方体同尺寸，轴对齐于世界坐标）
  gizmoHitBox = new THREE.Mesh(
    new THREE.BoxGeometry(0.98, 0.98, 0.98),
    new THREE.MeshBasicMaterial({ visible: false })
  )
  gizmoScene.add(gizmoHitBox)
}

// 让方向盒相机跟随主视角：方向盒保持轴对齐，迷你相机移到主视角同侧，
// 这样“主视角正在看哪个世界面，方向盒的那个面就正对屏幕”。
function syncGizmoCamera() {
  if (!gizmoCamera || !camera || !controls) return
  const dir = new THREE.Vector3().subVectors(camera.position, controls.target)
  if (dir.lengthSq() < 1e-8) dir.set(0, 0, 1)
  dir.normalize()
  gizmoCamera.position.copy(dir).multiplyScalar(2.3)
  gizmoCamera.quaternion.copy(camera.quaternion)
  gizmoCamera.updateMatrixWorld()
}

function onGizmoClick(event) {
  faceSelectFromPointer(event.clientX, event.clientY)
}

function faceSelectFromPointer(clientX, clientY) {
  if (!gizmoCamera || !gizmoHitBox || !rendered.value) return
  const canvas = gizmoCanvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  const ndcX = ((clientX - rect.left) / rect.width) * 2 - 1
  const ndcY = -(((clientY - rect.top) / rect.height) * 2 - 1)
  if (ndcX < -1 || ndcX > 1 || ndcY < -1 || ndcY > 1) return

  syncGizmoCamera()
  const raycaster = new THREE.Raycaster()
  raycaster.setFromCamera(new THREE.Vector2(ndcX, ndcY), gizmoCamera)
  const hits = raycaster.intersectObject(gizmoHitBox, false)
  if (!hits.length) return
  const p = hits[0].point // 命中盒位于世界原点且轴对齐，局部=世界
  const ax = Math.abs(p.x)
  const ay = Math.abs(p.y)
  const az = Math.abs(p.z)
  let side = null
  if (ax >= ay && ax >= az) side = p.x >= 0 ? '+X' : '-X'
  else if (ay >= ax && ay >= az) side = p.y >= 0 ? '+Y' : '-Y'
  else side = p.z >= 0 ? '+Z' : '-Z'
  const key = FACE_VIEW_MAP[side]
  if (!key) return
  activeView.value = key
  fitCamera()
  drawOnce()
}

// ---- 方向盒：按住拖拽旋转视角；轻点某面则跳转到该面 ----
const gizmoDrag = { active: false, moved: false, startX: 0, startY: 0, lastX: 0, lastY: 0 }
const GIZMO_ROTATE_SPEED = 0.012 // 每像素旋转弧度

function rotateCameraByDrag(dx, dy) {
  if (!camera || !controls) return
  const target = controls.target
  const offset = new THREE.Vector3().subVectors(camera.position, target)
  const sph = new THREE.Spherical().setFromVector3(offset)
  sph.theta -= dx * GIZMO_ROTATE_SPEED
  sph.phi -= dy * GIZMO_ROTATE_SPEED
  sph.phi = Math.max(0.02, Math.min(Math.PI - 0.02, sph.phi))
  offset.setFromSpherical(sph)
  camera.position.copy(target).add(offset)
  camera.lookAt(target)
  camera.updateProjectionMatrix()
}

function onGizmoPointerDown(event) {
  if (!rendered.value) return
  event.preventDefault()
  const canvas = gizmoCanvasRef.value
  if (canvas && canvas.setPointerCapture) {
    try { canvas.setPointerCapture(event.pointerId) } catch (e) { /* ignore */ }
  }
  gizmoDrag.active = true
  gizmoDrag.moved = false
  gizmoDrag.startX = event.clientX
  gizmoDrag.startY = event.clientY
  gizmoDrag.lastX = event.clientX
  gizmoDrag.lastY = event.clientY
}

function onGizmoPointerMove(event) {
  if (!gizmoDrag.active) return
  const dx = event.clientX - gizmoDrag.lastX
  const dy = event.clientY - gizmoDrag.lastY
  gizmoDrag.lastX = event.clientX
  gizmoDrag.lastY = event.clientY
  if (!gizmoDrag.moved && Math.hypot(event.clientX - gizmoDrag.startX, event.clientY - gizmoDrag.startY) > 4) {
    gizmoDrag.moved = true
  }
  if (gizmoDrag.moved && (dx || dy)) rotateCameraByDrag(dx, dy)
}

function onGizmoPointerUp(event) {
  if (!gizmoDrag.active) return
  const wasMove = gizmoDrag.moved
  gizmoDrag.active = false
  const canvas = gizmoCanvasRef.value
  if (canvas && canvas.releasePointerCapture) {
    try { canvas.releasePointerCapture(event.pointerId) } catch (e) { /* ignore */ }
  }
  if (!wasMove) faceSelectFromPointer(event.clientX, event.clientY)
}

function animate() {
  controls.update()
  renderer.render(scene, camera)
  if (gizmoRenderer && gizmoCamera && camera) {
    syncGizmoCamera()
    gizmoRenderer.render(gizmoScene, gizmoCamera)
  }
  rafId = requestAnimationFrame(animate)
}

const initScene = async () => {
  await nextTick()
  if (renderer || !canvasRef.value || !containerRef.value) return

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0b1220)

  const w = containerRef.value.clientWidth || 1
  const h = containerRef.value.clientHeight || 1
  camera = new THREE.PerspectiveCamera(35, w / h, 0.05, 5000)
  camera.position.set(80, 90, 120)

  renderer = new THREE.WebGLRenderer({ canvas: canvasRef.value, antialias: true, preserveDrawingBuffer: true })
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(w, h, false)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.12

  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(containerRef.value)

  buildGizmo()
  renderPath()
  animate()
}

watch(() => props.gcode, () => { renderPath() }, { flush: 'post' })

watch(() => props.validation.valid, (valid) => {
  if (valid) {
    if (!rendered.value) renderPath()
  } else {
    rendered.value = false
    lastBounds = null
  }
})

onMounted(initScene)

onBeforeUnmount(() => {
  cancelAnimationFrame(rafId)
  rafId = 0
  resizeObserver?.disconnect()
  resizeObserver = null
  disposeObject(cutObject)
  disposeObject(travelObject)
  disposeObject(decoGroup)
  cutObject = null
  travelObject = null
  decoGroup = null
  controls?.dispose()
  controls = null
  renderer?.dispose()
  renderer = null
  gizmoRenderer?.dispose()
  gizmoRenderer = null
  scene = null
  camera = null
  gizmoScene = null
  gizmoCube = null
  lastBounds = null
})
</script>
