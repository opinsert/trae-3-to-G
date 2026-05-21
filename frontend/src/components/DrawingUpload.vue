<template>
  <div class="bg-white rounded-xl shadow-lg p-6">
    <h2 class="text-xl font-bold text-gray-800 mb-6">工序图转换</h2>
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
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

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">手动填写工序卡信息</label>
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs text-gray-500 mb-1">产品名称</label>
              <input v-model="form.product_name" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">工序名称</label>
              <input v-model="form.process_name" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">工序编号</label>
              <input v-model="form.process_number" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">版本号</label>
              <input v-model="form.version" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">设备名称</label>
              <input v-model="form.equipment" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">数控系统</label>
              <input v-model="form.control_system" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">夹具名称</label>
              <input v-model="form.fixture" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">材料名称</label>
              <input v-model="form.material" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">刀具名称</label>
              <input v-model="form.tool_info.name" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">刀具直径(mm)</label>
              <input v-model.number="form.tool_info.diameter" type="number" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="mt-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">工步列表</label>
      <div class="space-y-3">
        <div v-for="(step, index) in validSteps" :key="step.sequence" class="flex items-center gap-3 bg-gray-50 rounded-lg p-3">
          <span class="w-8 h-8 flex items-center justify-center bg-blue-100 text-blue-600 rounded-full text-sm font-medium">{{ step.sequence }}</span>
          <input v-model="step.content" type="text" placeholder="工步内容" class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          <input v-model="step.parameters" type="text" placeholder="工艺参数（如 X=0, Y=0, Z=50）" class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          <input v-model="step.equipment" type="text" placeholder="使用设备" class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          <input v-model="step.remark" type="text" placeholder="备注" class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          <button @click="removeStep(index)" class="px-3 py-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors">
            <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div v-if="validSteps.length === 0" class="text-center text-gray-400 py-4">
          暂无工步
        </div>
      </div>
      <button @click="addStep" class="mt-3 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
        + 添加工步
      </button>
    </div>

    <div v-if="missingFields && missingFields.length > 0" class="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
      <p class="text-yellow-800 font-medium">请补充以下缺失的参数：</p>
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
  equipment: '立式加工中心',
  control_system: 'FANUC',
  fixture: '平口钳',
  material: '铝合金',
  tool_info: {
    name: '平底铣刀',
    length: 50,
    diameter: 8
  },
  steps: [
    { sequence: 1, content: '定位装夹', parameters: '', equipment: '', remark: '' },
    { sequence: 2, content: '钻孔加工', parameters: '', equipment: '', remark: '' }
  ]
})

const validSteps = computed(() => {
  if (!form.steps || !Array.isArray(form.steps)) {
    console.log('[前端] validSteps: 数组为空或不存在')
    return []
  }
  const valid = form.steps.filter(step => {
    return step && typeof step === 'object' && typeof step.content === 'string'
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
        console.log('  ├─ 产品名称:', data.product_name || '(空/未识别)')
        console.log('  ├─ 工序名称:', data.process_name || '(空/未识别)')
        console.log('  ├─ 工序编号:', data.process_number || '(空/未识别)')
        console.log('  ├─ 版本号:', data.version || '(空/未识别)')
        console.log('  ├─ 设备名称:', data.equipment || '(空/未识别)')
        console.log('  ├─ 数控系统:', data.control_system || '(空/未识别)')
        console.log('  ├─ 夹具名称:', data.fixture || '(空/未识别)')
        console.log('  ├─ 材料名称:', data.material || '(空/未识别)')
        console.log('  ├─ 刀具名称:', data.tool_name || '(空/未识别)')
        console.log('  ├─ 刀具长度:', data.tool_length || '(空/未识别)')
        console.log('  ├─ 刀具直径:', data.tool_diameter || '(空/未识别)')
        console.log('  ├─ 工步数量:', data.steps?.length || data.operations?.length || 0)
      
      const detectedSteps = data.steps || data.operations || []
      if (detectedSteps && detectedSteps.length > 0) {
        console.log('  └─ 工步详情:')
        detectedSteps.forEach((step, index) => {
          console.log(`      [工步${index + 1}]: sequence=${step.sequence}, content="${step.content}", parameters="${step.parameters}"`)
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
      
      if (data.product_name) {
        console.log('  → 更新: 产品名称 = "' + data.product_name + '"')
        form.product_name = data.product_name
      }
      if (data.process_name) {
        console.log('  → 更新: 工序名称 = "' + data.process_name + '"')
        form.process_name = data.process_name
      }
      if (data.process_number) {
        console.log('  → 更新: 工序编号 = "' + data.process_number + '"')
        form.process_number = data.process_number
      }
      if (data.version) {
        console.log('  → 更新: 版本号 = "' + data.version + '"')
        form.version = data.version
      }
      if (data.equipment) {
        console.log('  → 更新: 设备名称 = "' + data.equipment + '"')
        form.equipment = data.equipment
      }
      if (data.control_system) {
        console.log('  → 更新: 数控系统 = "' + data.control_system + '"')
        form.control_system = data.control_system
      }
      if (data.fixture) {
        console.log('  → 更新: 夹具名称 = "' + data.fixture + '"')
        form.fixture = data.fixture
      }
      if (data.material) {
        console.log('  → 更新: 材料名称 = "' + data.material + '"')
        form.material = data.material
      }
      if (data.tool_name) {
        console.log('  → 更新: 刀具名称 = "' + data.tool_name + '"')
        form.tool_info.name = data.tool_name
      }
      if (data.tool_length) {
        console.log('  → 更新: 刀具长度 = ' + data.tool_length)
        form.tool_info.length = data.tool_length
      }
      if (data.tool_diameter) {
        console.log('  → 更新: 刀具直径 = ' + data.tool_diameter)
        form.tool_info.diameter = data.tool_diameter
      }

      console.log('[前端-OCR] 【步骤6】处理工步数据')
      console.log('  - 当前表单工步数量:', form.steps.length)
      
      if (detectedSteps && Array.isArray(detectedSteps) && detectedSteps.length > 0) {
        console.log('  - 服务器返回的工步数量:', detectedSteps.length)
        
        const validSteps = detectedSteps.filter(step => {
          const isValid = step && typeof step === 'object' && typeof step.content === 'string'
          if (!isValid) {
            console.log('    ⚠ 跳过无效工步:', JSON.stringify(step))
          }
          return isValid
        }).map((step, index) => {
          const mapped = {
            sequence: index + 1,
            content: step.content || '',
            parameters: step.parameters || '',
            equipment: step.equipment || '',
            remark: step.remark || '',
            drawing_ref: step.drawing_ref || ''
          }
          console.log('    ✓ 映射工步' + (index + 1) + ':', JSON.stringify(mapped))
          return mapped
        })
        
        console.log('  - 过滤后的有效工步数量:', validSteps.length)
        
        if (validSteps.length > 0) {
          console.log('  → 替换表单工步列表')
          form.steps = validSteps
        } else {
          console.log('  ⚠ 没有有效的工步，保持原有列表')
        }
      } else {
        console.log('  ⚠ 服务器没有返回工步数据，保持原有列表')
      }

      console.log('[前端-OCR] 【步骤7】最终状态')
      console.log('  ├─ 产品名称:', form.product_name)
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
    sequence: form.steps.length + 1,
    content: '',
    parameters: '',
    equipment: '',
    remark: '',
    drawing_ref: ''
  })
}

const removeStep = (index) => {
  if (form.steps.length > 1) {
    form.steps.splice(index, 1)
    form.steps.forEach((step, i) => {
      step.sequence = i + 1
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