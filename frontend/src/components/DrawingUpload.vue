<template>
  <div class="bg-white rounded-xl shadow-lg p-6">
    <h2 class="text-xl font-bold text-gray-800 mb-6">工序图转换</h2>
    
    <!-- 格式切换 -->
    <div class="mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">工序卡格式</label>
      <div class="flex space-x-4">
        <label class="flex items-center">
          <input type="radio" v-model="formatType" value="type1" class="mr-2" />
          <span class="text-sm">格式1（设备+工序工时）</span>
        </label>
        <label class="flex items-center">
          <input type="radio" v-model="formatType" value="type2" class="mr-2" />
          <span class="text-sm">格式2（工位器具）</span>
        </label>
      </div>
    </div>

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
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 0 0 1115.9 6L16 6a5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
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
              <!-- 第一行：标签 -->
              <tr class="border-b border-gray-300">
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center w-1/4">车间</td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center w-1/4">工序号</td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center w-1/4">工序名称</td>
                <td class="bg-gray-100 px-2 py-1 font-medium text-center w-1/4">{{ materialLabel }}</td>
              </tr>
              <!-- 第二行：输入 -->
              <tr class="border-b border-gray-300">
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.workshop" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.process_card_number" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.process_name" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="px-2 py-1">
                  <input v-model="form.material_grade" type="text" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
              <!-- 第三行：标签 -->
              <tr class="border-b border-gray-300">
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center">毛坯种类</td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center">{{ blankSizeLabel }}</td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center">{{ blankAvailableLabel }}</td>
                <td class="bg-gray-100 px-2 py-1 font-medium text-center">每台件数</td>
              </tr>
              <!-- 第四行：输入 -->
              <tr class="border-b border-gray-300">
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.blank_type" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.blank_size" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model.number="form.blank_available_pieces" type="number" class="w-full border-none focus:ring-0" />
                </td>
                <td class="px-2 py-1">
                  <input v-model.number="form.pieces_per_machine" type="number" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
              <!-- 第五行：标签 - 根据格式变化 -->
              <tr class="border-b border-gray-300" v-if="formatType === 'type1'">
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center">夹具编号</td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center">夹具名称</td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center">每台件数</td>
                <td class="bg-gray-100 px-2 py-1 font-medium text-center">切削液</td>
              </tr>
              <!-- 第五行：输入 - 格式1 -->
              <tr class="border-b border-gray-300" v-if="formatType === 'type1'">
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.fixture_no" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.fixture" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model.number="form.pieces_per_machine" type="number" class="w-full border-none focus:ring-0" />
                </td>
                <td class="px-2 py-1">
                  <input v-model="form.cutting_fluid" type="text" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
              <!-- 第五行：标签 - 格式2 -->
              <tr class="border-b border-gray-300" v-if="formatType === 'type2'">
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center">设备名称</td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center">设备型号</td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center">设备编号</td>
                <td class="bg-gray-100 px-2 py-1 font-medium text-center">同时加工件数</td>
              </tr>
              <!-- 第五行：输入 - 格式2 -->
              <tr class="border-b border-gray-300" v-if="formatType === 'type2'">
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.equipment" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.equipment_model" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.equipment_no" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="px-2 py-1">
                  <input v-model.number="form.simultaneous_pieces" type="number" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
              <!-- 第六行：标签 - 格式1 -->
              <tr class="border-b border-gray-300" v-if="formatType === 'type1'">
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center">设备名称</td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center">设备型号</td>
                <td class="bg-gray-100 px-2 py-1 font-medium text-center" colspan="2">工序工时</td>
              </tr>
              <!-- 第六行：输入 - 格式1 -->
              <tr class="border-b border-gray-300" v-if="formatType === 'type1'">
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.equipment" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.equipment_model" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center">准终</td>
                <td class="bg-gray-100 px-2 py-1 font-medium text-center">单件</td>
              </tr>
              <!-- 第七行：输入 - 格式1 -->
              <tr v-if="formatType === 'type1'">
                <td class="border-r border-gray-300 bg-gray-50 px-2 py-1"></td>
                <td class="border-r border-gray-300 bg-gray-50 px-2 py-1"></td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model.number="form.preparation_time" type="number" class="w-full border-none focus:ring-0" />
                </td>
                <td class="px-2 py-1">
                  <input v-model.number="form.unit_time" type="number" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
              <!-- 第六行：标签 - 格式2 -->
              <tr class="border-b border-gray-300" v-if="formatType === 'type2'">
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center">夹具编号</td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center">夹具名称</td>
                <td class="bg-gray-100 px-2 py-1 font-medium text-center" colspan="2">切削液</td>
              </tr>
              <!-- 第六行：输入 - 格式2 -->
              <tr v-if="formatType === 'type2'">
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.fixture_no" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.fixture" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="px-2 py-1" colspan="2">
                  <input v-model="form.cutting_fluid" type="text" class="w-full border-none focus:ring-0" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 工位器具和工时 - 仅格式2显示 -->
        <div class="border border-gray-300 rounded-lg overflow-hidden" v-if="formatType === 'type2'">
          <table class="w-full text-sm">
            <tbody>
              <!-- 第一行：标签 -->
              <tr class="border-b border-gray-300">
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center w-1/4">工位器具编号</td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center w-1/4">工位器具名称</td>
                <td class="bg-gray-100 px-2 py-1 font-medium text-center" colspan="2">工序工时（分）</td>
              </tr>
              <!-- 第二行：标签 -->
              <tr class="border-b border-gray-300">
                <td class="border-r border-gray-300 bg-gray-50 px-2 py-1"></td>
                <td class="border-r border-gray-300 bg-gray-50 px-2 py-1"></td>
                <td class="border-r border-gray-300 bg-gray-100 px-2 py-1 font-medium text-center">准终</td>
                <td class="bg-gray-100 px-2 py-1 font-medium text-center">单件</td>
              </tr>
              <!-- 第三行：输入 -->
              <tr>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.station_tool_no" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model="form.station_tool_name" type="text" class="w-full border-none focus:ring-0" />
                </td>
                <td class="border-r border-gray-300 px-2 py-1">
                  <input v-model.number="form.preparation_time" type="number" class="w-full border-none focus:ring-0" />
                </td>
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
const formatType = ref('type2') // 默认格式2

// 动态标签
const materialLabel = computed(() => formatType.value === 'type1' ? '材料号' : '材料牌号')
const blankSizeLabel = computed(() => formatType.value === 'type1' ? '外形尺寸' : '毛坯外形尺寸')
const blankAvailableLabel = computed(() => formatType.value === 'type1' ? '每毛坯可制件数' : '毛坯还可制件数')

const form = reactive({
  product_name: '测试产品',
  process_name: '钻孔',
  process_number: 'OP-001',
  version: 'V1.0',
  equipment: '钻床',
  control_system: '',
  fixture: '',
  material: '',
  tool_name: '平底铣刀',
  tool_length: 50,
  tool_diameter: 8,
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
  ],
  operations: [
    {
      sequence: 1,
      content: '钻孔 M8',
      parameters: '',
      equipment: 'Φ7 麻花钻',
      remark: ''
    },
    {
      sequence: 2,
      content: '攻螺纹 M8',
      parameters: '',
      equipment: '',
      remark: ''
    }
  ]
})

const validSteps = computed(() => {
  if (!form.steps || !Array.isArray(form.steps)) {
    return []
  }
  return form.steps
})

const validMissingFields = computed(() => {
  if (!missingFields.value || !Array.isArray(missingFields.value)) {
    return []
  }
  return missingFields.value
})

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleDrop = (e) => {
  const files = e.dataTransfer.files
  if (files.length > 0) {
    handleFile(files[0])
  }
}

const handleFileSelect = (e) => {
  if (e.target.files?.length > 0) {
    handleFile(e.target.files[0])
  }
}

const handleFile = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedImage.value = e.target.result
  }
  reader.onerror = () => {
    console.error('[前端] 文件读取失败:', reader.error)
    alert('文件读取失败，请重试')
  }
  reader.readAsDataURL(file)
}

const extractFromImage = async () => {
  if (!uploadedImage.value) {
    alert('请先上传图片')
    return
  }

  extracting.value = true
  try {
    const response = await drawingApi.ocrExtract(uploadedImage.value)
    const extractedData = response.data?.data || response.data
    if (extractedData) {
      // 填充表单数据
      Object.keys(extractedData).forEach(key => {
        if (key in form) {
          if (key === 'steps' || key === 'drawing_steps' || key === 'operations') {
            // 处理数组数据
            const data = extractedData[key]
            if (data && Array.isArray(data) && data.length > 0) {
              if (key === 'drawing_steps') {
                form.steps = data.map((step, index) => ({
                  ...step,
                  step: step.step || index + 1
                }))
              } else if (key === 'steps') {
                form.operations = data.map((step, index) => ({
                  sequence: step.step || index + 1,
                  content: step.step_content || '',
                  parameters: '',
                  equipment: step.tooling || '',
                  remark: ''
                }))
              } else {
                form[key] = data
              }
            }
          } else {
            // 处理基本字段，智能转换类型
            const value = extractedData[key]
            if (value !== null && value !== undefined && value !== '') {
              form[key] = value
            }
          }
        }
      })

      // 处理 drawing_steps 兼容
      if (extractedData.drawing_steps && Array.isArray(extractedData.drawing_steps) && extractedData.drawing_steps.length > 0) {
        form.steps = extractedData.drawing_steps.map((step, index) => ({
          ...step,
          step: step.step || index + 1
        }))
        form.operations = extractedData.drawing_steps.map((step, index) => ({
          sequence: step.step || index + 1,
          content: step.step_content || '',
          parameters: '',
          equipment: step.tooling || '',
          remark: ''
        }))
      }
    }
    alert('信息提取成功！')
  } catch (error) {
    console.error('提取失败:', error)
    const detail = error.response?.data?.detail || error.message || '未知错误'
    alert(`信息提取失败: ${detail}`)
  } finally {
    extracting.value = false
  }
}

const addStep = () => {
  const newStep = {
    step: (form.steps?.length || 0) + 1,
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
  }
  if (!form.steps) {
    form.steps = []
  }
  form.steps.push(newStep)
}

const removeStep = (index) => {
  if (form.steps) {
    form.steps.splice(index, 1)
    // 重新编号
    form.steps.forEach((step, i) => {
      step.step = i + 1
    })
  }
}

const convert = async () => {
  loading.value = true
  missingFields.value = []
  try {
    // 构建发送给后端的数据，兼容旧格式
    const payload = {
      ...form,
      // 同时发送旧格式和新格式
      drawing_steps: form.steps,
      steps: form.steps
    }
    
    await emit('convert', payload)
  } catch (error) {
    if (error.response?.data?.missing_fields) {
      missingFields.value = error.response.data.missing_fields
    } else {
      console.error('转换失败:', error)
      const detail = error.response?.data?.detail || error.message || '未知错误'
      alert(`转换失败: ${detail}`)
    }
  } finally {
    loading.value = false
  }
}
</script>
