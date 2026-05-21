<template>
  <div class="bg-white rounded-xl shadow-lg p-6">
    <h2 class="text-xl font-bold text-gray-800 mb-6">工序图转换</h2>
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 左栏：图片上传 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">上传工序图</label>
        <div
          @click="triggerUpload"
          @dragover.prevent
          @drop.prevent="handleDrop"
          class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 hover:bg-blue-50 cursor-pointer transition-all"
        >
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            @change="handleFileSelect"
            class="hidden"
          />
          <svg class="mx-auto h-12 w-12 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p class="mt-2 text-sm text-gray-600">点击或拖拽上传工序图</p>
          <p class="mt-1 text-xs text-gray-400">支持 JPG、PNG、PDF 等格式</p>
        </div>
        
        <div v-if="uploadedImage" class="mt-4">
          <img :src="uploadedImage" alt="工序图预览" class="max-w-full rounded-lg border border-gray-200" />
          <button 
            v-if="uploadedImage"
            @click="extractFromImage"
            :disabled="extracting"
            class="mt-4 w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {{ extracting ? '识别中...' : '从图片中提取信息' }}
          </button>
        </div>
      </div>

      <!-- 右栏：工序卡表单 -->
      <div class="space-y-4">
        <!-- 工序卡基本信息表格 -->
        <div class="border border-gray-300 rounded-lg overflow-hidden">
          <table class="w-full text-sm">
            <tbody>
              <!-- 第1行 -->
              <tr class="border-b border-gray-300">
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium w-1/4">车间</td>
                <td class="border-r border-gray-300 px-2 py-1 w-1/4">
                  <input v-model="form.workshop" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium w-1/4">工序号</td>
                <td class="px-2 py-1 w-1/4">
                  <input v-model="form.process_card_number" type="text" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
              <!-- 第2行 -->
              <tr class="border-b border-gray-300">
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">工序名称</td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.process_name" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">材料牌号</td>
                <td class="px-2 py-1">
                  <input v-model="form.material_grade" type="text" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
              <!-- 第3行 -->
              <tr class="border-b border-gray-300">
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">毛坯种类</td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.blank_type" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">毛坯外形尺寸</td>
                <td class="px-2 py-1">
                  <input v-model="form.blank_size" type="text" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
              <!-- 第4行 -->
              <tr class="border-b border-gray-300">
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">毛坯还可制件数</td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model.number="form.blank_available_pieces" type="number" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">每台件数</td>
                <td class="px-2 py-1">
                  <input v-model.number="form.pieces_per_machine" type="number" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
              <!-- 第5行 -->
              <tr class="border-b border-gray-300">
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">设备名称</td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.equipment" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">设备型号</td>
                <td class="px-2 py-1">
                  <input v-model="form.equipment_model" type="text" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
              <!-- 第6行 -->
              <tr class="border-b border-gray-300">
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">设备编号</td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.equipment_no" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">同时加工件数</td>
                <td class="px-2 py-1">
                  <input v-model.number="form.simultaneous_pieces" type="number" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
              <!-- 第7行 -->
              <tr>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">夹具编号</td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.fixture_no" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">夹具名称</td>
                <td class="px-2 py-1">
                  <input v-model="form.fixture" type="text" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 切削液单独一行 -->
        <div class="border border-gray-300 rounded-lg overflow-hidden">
          <table class="w-full text-sm">
            <tbody>
              <tr>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium w-1/4">切削液</td>
                <td class="px-2 py-1 w-3/4">
                  <input v-model="form.cutting_fluid" type="text" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 工位器具和工时 -->
        <div class="border border-gray-300 rounded-lg overflow-hidden">
          <table class="w-full text-sm">
            <tbody>
              <tr>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">工位器具编号</td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.station_tool_no" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">工位器具名称</td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.station_tool_name" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="bg-gray-100 px-2 py-1 font-medium" colspan="2">工序工时（分）</td>
              </tr>
              <tr>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium" colspan="2"></td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium" colspan="2"></td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">准终</td>
                <td class="px-2 py-1">
                  <input v-model.number="form.preparation_time" type="number" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
              <tr>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium" colspan="2"></td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium" colspan="2"></td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium">单件</td>
                <td class="px-2 py-1">
                  <input v-model.number="form.unit_time" type="number" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 工步表格 -->
    <div class="mt-6">
      <div class="border border-gray-300 rounded-lg overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-100 border-b border-gray-300">
              <th class="border-r border-gray-300 px-2 py-1 font-medium w-12">工步号</th>
              <th class="border-r border-gray-300 px-2 py-1 font-medium">工步内容</th>
              <th class="border-r border-gray-300 px-2 py-1 font-medium">工艺装备</th>
              <th class="border-r border-gray-300 px-2 py-1 font-medium">主轴转速r/min</th>
              <th class="border-r border-gray-300 px-2 py-1 font-medium">切削速度m/min</th>
              <th class="border-r border-gray-300 px-2 py-1 font-medium">进给量mm/r</th>
              <th class="border-r border-gray-300 px-2 py-1 font-medium">被吃刀量mm</th>
              <th class="border-r border-gray-300 px-2 py-1 font-medium">进给次数</th>
              <th class="border-r border-gray-300 px-2 py-1 font-medium" colspan="2">工时/min</th>
              <th class="px-2 py-1 font-medium w-20">操作</th>
            </tr>
            <tr class="bg-gray-50 border-b border-gray-300">
              <th class="border-r border-gray-300 px-2 py-1" colspan="8"></th>
              <th class="border-r border-gray-300 px-2 py-1 font-medium text-xs">机动</th>
              <th class="border-r border-gray-300 px-2 py-1 font-medium text-xs">辅助</th>
              <th class="px-2 py-1"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(step, index) in validSteps" :key="step.step" class="border-b border-gray-200">
              <td class="border-r border-gray-300 px-2 py-1 text-center">{{ step.step }}</td>
              <td class="border-r border-gray-300 px-2 py-1">
                <input v-model="step.step_content" type="text" class="w-full border-none focus:ring-0" />
              </td>
              <td class="border-r border-gray-300 px-2 py-1">
                <input v-model="step.tooling" type="text" class="w-full border-none focus:ring-0" />
              </td>
              <td class="border-r border-gray-300 px-2 py-1">
                <input v-model.number="step.spindle_speed" type="number" class="w-full border-none focus:ring-0" />
              </td>
              <td class="border-r border-gray-300 px-2 py-1">
                <input v-model.number="step.cutting_speed" type="number" class="w-full border-none focus:ring-0" />
              </td>
              <td class="border-r border-gray-300 px-2 py-1">
                <input v-model.number="step.feed_rate" type="number" class="w-full border-none focus:ring-0" />
              </td>
              <td class="border-r border-gray-300 px-2 py-1">
                <input v-model.number="step.depth_of_cut" type="number" class="w-full border-none focus:ring-0" />
              </td>
              <td class="border-r border-gray-300 px-2 py-1">
                <input v-model.number="step.feed_count" type="number" class="w-full border-none focus:ring-0" />
              </td>
              <td class="border-r border-gray-300 px-2 py-1">
                <input v-model.number="step.machine_time" type="number" class="w-full border-none focus:ring-0" />
              </td>
              <td class="border-r border-gray-300 px-2 py-1">
                <input v-model.number="step.auxiliary_time" type="number" class="w-full border-none focus:ring-0" />
              </td>
              <td class="px-2 py-1 text-center">
                <button @click="removeStep(index)" class="text-red-500 hover:text-red-700">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <button @click="addStep" class="mt-3 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
        + 添加工步
      </button>
    </div>

    <div v-if="missingFields && missingFields.length > 0" class="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
      <p class="text-yellow-800 font-medium">请补充以下缺失的字段：</p>
      <ul class="mt-2 space-y-1">
        <li v-for="(field, index) in validMissingFields" :key="index" class="text-yellow-700">
          - {{ field }}
        </li>
      </ul>
    </div>

    <div class="mt-6 flex space-x-4">
      <button
        @click="convert"
        :disabled="loading"
        class="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      >
        <span v-if="loading">转换中...</span>
        <span v-else>生成G代码</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { drawingApi } from '../api'

const emit = defineEmits(['convert'])

const fileInput = ref(null)
const uploadedImage = ref('')
const loading = ref(false)
const extracting = ref(false)
const missingFields = ref([])

const form = reactive({
  product_name: '测试产品',
  process_name: '钻孔',
  process_number: 'OP-001',
  version: 'V1.0',
  equipment: '钻床',
  control_system: '',
  fixture: '',
  material: '',
  tool_info: {
    name: '平底铣刀',
    length: 50,
    diameter: 8
  },
  workshop: '金工',
  process_card_number: '5',
  material_grade: '45',
  blank_type: '铸件',
  blank_size: '',
  blank_available_pieces: null,
  pieces_per_machine: null,
  equipment_model: 'Z535',
  equipment_no: '05',
  simultaneous_pieces: null,
  fixture_no: '',
  cutting_fluid: '',
  station_tool_no: '',
  station_tool_name: '',
  preparation_time: null,
  unit_time: null,
  steps: [
    {
      step: 1,
      step_content: '钻孔 M8',
      tooling: 'Φ7 麻花钻',
      spindle_speed: 750,
      cutting_speed: 16.49,
      feed_rate: 0.2,
      depth_of_cut: null,
      feed_count: 1,
      machine_time: 0.14,
      auxiliary_time: null,
      remark: ''
    },
    {
      step: 2,
      step_content: '攻螺纹 M8',
      tooling: '',
      spindle_speed: null,
      cutting_speed: null,
      feed_rate: null,
      depth_of_cut: null,
      feed_count: null,
      machine_time: null,
      auxiliary_time: null,
      remark: ''
    }
  ]
})

const validSteps = computed(() => {
  if (!form.steps || !Array.isArray(form.steps)) {
    console.log('[前端] validSteps: 数组为空或不存在')
    return []
  }
  const valid = form.steps.filter(step => {
    return step && typeof step === 'object' && typeof step.step_content === 'string'
  })
  console.log('[前端] validSteps:', valid.length, '个有效工步')
  return valid
})

const validMissingFields = computed(() => {
  if (!missingFields.value || !Array.isArray(missingFields.value)) {
    return []
  }
  return missingFields.value.filter(field => typeof field === 'string')
})

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (file) {
    console.log('[前端] 选择文件:', file.name, file.size, 'bytes')
    const reader = new FileReader()
    reader.onload = (e) => {
      uploadedImage.value = e.target?.result
      console.log('[前端] 文件读取完成，长度:', uploadedImage.value.length)
    }
    reader.readAsDataURL(file)
  }
}

const handleDrop = (event) => {
  const file = event.dataTransfer?.files?.[0]
  if (file && file.type.startsWith('image/')) {
    console.log('[前端] 拖拽文件:', file.name, file.size, 'bytes')
    const reader = new FileReader()
    reader.onload = (e) => {
      uploadedImage.value = e.target?.result
      console.log('[前端] 拖拽文件读取完成，长度:', uploadedImage.value.length)
    }
    reader.readAsDataURL(file)
  }
}

const extractFromImage = async () => {
  if (!uploadedImage.value) {
    alert('请先上传图片')
    return
  }

  extracting.value = true
  console.log('='.repeat(80))
  console.log('[前端-OCR] ================== 开始OCR识别流程 ==================')
  console.log('='.repeat(80))
  
  console.log('[前端-OCR] 【步骤1】图片数据准备')
  console.log('  - 图片是否存在:', !!uploadedImage.value)
  console.log('  - 图片数据长度:', uploadedImage.value.length, '字符')
  console.log('  - 图片数据前缀:', uploadedImage.value.substring(0, 80))
  console.log('  - 数据格式:', uploadedImage.value.substring(0, uploadedImage.value.indexOf(',')))

  try {
    console.log('[前端-OCR] 【步骤2】发送OCR识别请求到后端')
    console.log('  - 请求URL: POST /api/v1/drawing/ocr-extract')
    console.log('  - 图片数据长度:', uploadedImage.value.length)
    
    const response = await drawingApi.ocrExtract(uploadedImage.value)
    
    console.log('[前端-OCR] 【步骤3】收到服务器响应')
      console.log('  - HTTP状态码:', response.status)
      console.log('  - 响应数据:', JSON.stringify(response.data, null, 2))
      
      if (response.data.success) {
        console.log('[前端-OCR] ✓ OCR识别成功 (success=true)')
        const data = response.data.data
        
        // 打印表格识别结果（如果有）
        if (data.table_data) {
          console.log('[前端-OCR] 【步骤3.5】表格识别结果')
          console.log('  ├─ 表格数据:', JSON.stringify(data.table_data, null, 2).substring(0, 1000))
          console.log('  └─ (表格数据已截断，查看完整数据请查看后端日志)')
        }
        
        console.log('[前端-OCR] 【步骤4】解析识别结果')
        console.log('  ├─ 车间:', data.workshop || '(空/未识别)')
        console.log('  ├─ 工序号:', data.process_card_number || '(空/未识别)')
        console.log('  ├─ 工序名称:', data.process_name || '(空/未识别)')
        console.log('  ├─ 材料牌号:', data.material_grade || '(空/未识别)')
        console.log('  ├─ 毛坯种类:', data.blank_type || '(空/未识别)')
        console.log('  ├─ 毛坯外形尺寸:', data.blank_size || '(空/未识别)')
        console.log('  ├─ 毛坯还可制件数:', data.blank_available_pieces || '(空/未识别)')
        console.log('  ├─ 每台件数:', data.pieces_per_machine || '(空/未识别)')
        console.log('  ├─ 设备名称:', data.equipment || '(空/未识别)')
        console.log('  ├─ 设备型号:', data.equipment_model || '(空/未识别)')
        console.log('  ├─ 设备编号:', data.equipment_no || '(空/未识别)')
        console.log('  ├─ 同时加工件数:', data.simultaneous_pieces || '(空/未识别)')
        console.log('  ├─ 夹具编号:', data.fixture_no || '(空/未识别)')
        console.log('  ├─ 夹具名称:', data.fixture || '(空/未识别)')
        console.log('  ├─ 切削液:', data.cutting_fluid || '(空/未识别)')
        console.log('  ├─ 工位器具编号:', data.station_tool_no || '(空/未识别)')
        console.log('  ├─ 工位器具名称:', data.station_tool_name || '(空/未识别)')
        console.log('  ├─ 准终工时:', data.preparation_time || '(空/未识别)')
        console.log('  ├─ 单件工时:', data.unit_time || '(空/未识别)')
        
        const detectedSteps = data.drawing_steps || data.steps || data.operations || []
        console.log('  ├─ 工步数量:', detectedSteps.length)
        if (detectedSteps && detectedSteps.length > 0) {
          console.log('  └─ 工步详情:')
          detectedSteps.forEach((step, index) => {
            console.log(`      [工步${index + 1}]:`, JSON.stringify(step))
          })
        } else {
          console.log('  └─ 工步详情: 无')
        }
        
        if (data.raw_text) {
          console.log('  ├─ 原始文本长度:', data.raw_text.length, '字符')
          console.log('  ├─ 原始文本内容预览:')
          console.log('  |  ' + '-'.repeat(76))
          const lines = data.raw_text.split('\n').slice(0, 10)
          lines.forEach(line => {
            console.log('  |  ' + line)
          })
          if (data.raw_text.split('\n').length > 10) {
            console.log('  |  ... (还有', data.raw_text.split('\n').length - 10, '行)')
          }
          console.log('  |  ' + '-'.repeat(76))
        } else {
          console.log('  ├─ 原始文本: (无)')
        }
        
        if (data.error) {
          console.log('  └─ ⚠ 识别警告:', data.error)
        }
        
        console.log('[前端-OCR] 【步骤5】填充表单数据')
        
        if (data.workshop !== undefined) form.workshop = data.workshop
        if (data.process_card_number !== undefined) form.process_card_number = data.process_card_number
        if (data.process_name !== undefined) form.process_name = data.process_name
        if (data.material_grade !== undefined) form.material_grade = data.material_grade
        if (data.blank_type !== undefined) form.blank_type = data.blank_type
        if (data.blank_size !== undefined) form.blank_size = data.blank_size
        if (data.blank_available_pieces !== undefined) form.blank_available_pieces = data.blank_available_pieces
        if (data.pieces_per_machine !== undefined) form.pieces_per_machine = data.pieces_per_machine
        if (data.equipment !== undefined) form.equipment = data.equipment
        if (data.equipment_model !== undefined) form.equipment_model = data.equipment_model
        if (data.equipment_no !== undefined) form.equipment_no = data.equipment_no
        if (data.simultaneous_pieces !== undefined) form.simultaneous_pieces = data.simultaneous_pieces
        if (data.fixture_no !== undefined) form.fixture_no = data.fixture_no
        if (data.fixture !== undefined) form.fixture = data.fixture
        if (data.cutting_fluid !== undefined) form.cutting_fluid = data.cutting_fluid
        if (data.station_tool_no !== undefined) form.station_tool_no = data.station_tool_no
        if (data.station_tool_name !== undefined) form.station_tool_name = data.station_tool_name
        if (data.preparation_time !== undefined) form.preparation_time = data.preparation_time
        if (data.unit_time !== undefined) form.unit_time = data.unit_time

        console.log('[前端-OCR] 【步骤6】处理工步数据')
        console.log('  - 当前表单工步数量:', form.steps.length)
        
        if (detectedSteps && Array.isArray(detectedSteps) && detectedSteps.length > 0) {
          console.log('  - 服务器返回的工步数量:', detectedSteps.length)
          
          const validStepList = detectedSteps.filter(step => {
            const isValid = step && typeof step === 'object'
            if (!isValid) {
              console.log('    ⚠ 跳过无效工步:', JSON.stringify(step))
            }
            return isValid
          }).map((step, index) => {
            const mapped = {
              step: step.step || step.sequence || index + 1,
              step_content: step.step_content || step.content || '',
              tooling: step.tooling || step.equipment || '',
              spindle_speed: step.spindle_speed !== undefined ? step.spindle_speed : null,
              cutting_speed: step.cutting_speed !== undefined ? step.cutting_speed : null,
              feed_rate: step.feed_rate !== undefined ? step.feed_rate : null,
              depth_of_cut: step.depth_of_cut !== undefined ? step.depth_of_cut : null,
              feed_count: step.feed_count !== undefined ? step.feed_count : null,
              machine_time: step.machine_time !== undefined ? step.machine_time : null,
              auxiliary_time: step.auxiliary_time !== undefined ? step.auxiliary_time : null,
              remark: step.remark || ''
            }
            console.log('    ✓ 映射工步' + (index + 1) + ':', JSON.stringify(mapped))
            return mapped
          })
          
          console.log('  - 过滤后的有效工步数量:', validStepList.length)
          
          if (validStepList.length > 0) {
            console.log('  → 替换表单工步列表')
            form.steps = validStepList
          } else {
            console.log('  ⚠ 没有有效的工步，保持原有列表')
          }
        } else {
          console.log('  ⚠ 服务器没有返回工步数据，保持原有列表')
        }

        console.log('[前端-OCR] 【步骤7】最终状态')
        console.log('  ├─ 车间:', form.workshop)
        console.log('  ├─ 工序名称:', form.process_name)
        console.log('  ├─ 设备名称:', form.equipment)
        console.log('  ├─ 工步数量:', form.steps.length)
        console.log('  └─ 工步:', JSON.stringify(form.steps))
        console.log('[前端-OCR] ✓ OCR识别流程完成')
        console.log('='.repeat(80))
        
        alert('信息提取成功！请检查并补充缺失字段')
      } else {
        console.error('[前端-OCR] ✗ OCR识别失败')
        console.error('[前端-OCR]  - 错误信息:', response.data.message || '未知错误')
        console.error('[前端-OCR]  - 缺失字段:', response.data.missing_fields || [])
        console.log('='.repeat(80))
        alert('图片识别失败，请手动填写')
      }
  } catch (error) {
    console.error('[前端-OCR] ✗ 请求失败')
    console.error('  - 错误类型:', error.name)
    console.error('  - 错误信息:', error.message)
    if (error.response) {
      console.error('  - HTTP状态码:', error.response.status)
      console.error('  - 响应数据:', JSON.stringify(error.response.data, null, 2))
    }
    console.error('  - 完整错误:', error)
    console.log('='.repeat(80))
    alert('识别失败，请手动填写')
  } finally {
    extracting.value = false
  }
}

const addStep = () => {
  form.steps.push({
    step: form.steps.length + 1,
    step_content: '',
    tooling: '',
    spindle_speed: null,
    cutting_speed: null,
    feed_rate: null,
    depth_of_cut: null,
    feed_count: null,
    machine_time: null,
    auxiliary_time: null,
    remark: ''
  })
}

const removeStep = (index) => {
  if (form.steps.length > 1) {
    form.steps.splice(index, 1)
    form.steps.forEach((step, i) => {
      step.step = i + 1
    })
  }
}

const convert = async () => {
  loading.value = true
  missingFields.value = []
  
  console.log('[前端-转换] 开始转换流程')
  console.log('[前端-转换] 表单数据:', JSON.stringify(form, null, 2))
  console.log('[前端-转换] 有效工步:', JSON.stringify(validSteps.value, null, 2))
  
  try {
    const response = await drawingApi.convert(form, validSteps.value)
    console.log('[前端-转换] 收到响应:', JSON.stringify(response.data, null, 2))
    
    if (response.data.success) {
      if (response.data.data) {
        console.log('[前端-转换] ✓ 转换成功')
        emit('convert', response.data.data)
      } else {
        console.error('[前端-转换] ✗ 成功响应但没有数据')
        alert('转换成功但没有返回数据')
      }
    } else {
      missingFields.value = response.data.missing_fields || []
      console.log('[前端-转换] ⚠ 缺失字段:', missingFields.value)
    }
  } catch (error) {
    console.error('[前端-转换] ✗ 转换失败:', error)
    console.error('[前端-转换] 错误详情:', error.response?.data || error.message)
    alert('转换失败，请查看控制台了解详细错误')
  } finally {
    loading.value = false
  }
}
</script>
