<template>
  <div class="bg-white rounded-xl shadow-lg p-6">
    <h2 class="text-xl font-bold text-gray-800 mb-6">自然语言转换</h2>
    
    <div class="mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">输入工序卡信息</label>
      <textarea
        v-model="inputText"
        rows="10"
        @input="handleInput"
        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none transition-all"
        placeholder="请输入完整的工序卡信息，包括：&#10;产品名称、工序名称、工序编号、版本号、设备名称、数控系统、夹具名称、材料名称、刀具信息以及操作步骤&#10;&#10;示例：&#10;产品名称：铝合金外壳&#10;工序名称：平面铣削&#10;工序编号：OP001&#10;版本号：V1.0&#10;设备名称：CNC加工中心&#10;数控系统：FANUC 0i-MF&#10;夹具名称：真空吸盘&#10;材料名称：6061铝合金&#10;刀具名称：立铣刀，长度：75mm，直径：10mm&#10;&#10;操作步骤：&#10;1. 快速定位到安全高度，X=0，Y=0，Z=50&#10;2. 铣削平面，X=100，Y=100，Z=-2，F=150&#10;3. 抬刀返回，Z=50"
      ></textarea>
    </div>

    <div class="grid grid-cols-2 gap-6 mb-6">
      <div class="p-4 bg-green-50 border border-green-200 rounded-lg">
        <h3 class="text-sm font-medium text-green-800 mb-2 flex items-center">
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
          </svg>
          已满足的参数
        </h3>
        <ul class="mt-2 space-y-1">
          <li v-for="field in filledFields" :key="field" class="text-sm text-green-700">
            - {{ fieldMap[field] || field }}
          </li>
          <li v-if="filledFields.length === 0" class="text-sm text-green-400 italic">
            暂无已满足的参数
          </li>
        </ul>
      </div>

      <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
        <h3 class="text-sm font-medium text-red-800 mb-2 flex items-center">
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
          缺失的参数
        </h3>
        <ul class="mt-2 space-y-1">
          <li v-for="field in missingFields" :key="field" class="text-sm text-red-700">
            - {{ fieldMap[field] || field }}
          </li>
          <li v-if="missingFields.length === 0" class="text-sm text-red-400 italic">
            所有参数已满足
          </li>
        </ul>
      </div>
    </div>

    <div class="flex space-x-4">
      <button
        @click="handleConvert"
        :disabled="loading || missingFields.length > 0"
        class="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      >
        <span v-if="loading" class="flex items-center justify-center">
          <svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          转换中...
        </span>
        <span v-else>生成G代码</span>
      </button>
      
      <button
        @click="handleClear"
        class="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 focus:ring-4 focus:ring-gray-200 transition-all"
      >
        清空
      </button>
    </div>

    <div class="mt-6 p-4 bg-gray-50 rounded-lg">
      <h3 class="text-sm font-medium text-gray-700 mb-2">参数说明</h3>
      <p class="text-sm text-gray-600">系统将根据您输入的自然语言自动提取工序卡参数，并生成对应的G代码。如果参数不完整，系统会提示您补充缺失的信息。</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { naturalLanguageApi } from '../api'

const emit = defineEmits(['convert'])

const inputText = ref('')
const loading = ref(false)

const fieldMap = {
  product_name: '产品名称',
  process_name: '工序名称',
  process_number: '工序编号',
  version: '版本号',
  equipment: '设备名称',
  control_system: '数控系统',
  fixture: '夹具名称',
  material: '材料名称',
  tool_name: '刀具名称',
  tool_length: '刀具长度',
  tool_diameter: '刀具直径'
}

const REQUIRED_FIELDS = [
  'product_name', 'process_name', 'process_number', 'version',
  'equipment', 'control_system', 'fixture', 'material',
  'tool_name', 'tool_length', 'tool_diameter'
]

const fieldPatterns = {
  product_name: [/产品名称[：:]\s*([^|，。\n]+)/, /\*\*产品名称\*\*[^\|]*\|([^\|]+)/],
  process_name: [/工序名称[：:]\s*([^|，。\n]+)/, /\*\*工序名称\*\*[^\|]*\|([^\|]+)/],
  process_number: [/工序编号[：:]\s*([^|，。\n]+)/, /\*\*工序编号\*\*[^\|]*\|([^\|]+)/],
  version: [/版本号[：:]\s*([^|，。\n]+)/, /\*\*版本号\*\*[^\|]*\|([^\|]+)/, /[-]\s*版本号[：:]\s*([^|，。\n]+)/],
  equipment: [/设备名称[：:]\s*([^|，。\n]+)/, /\*\*设备名称\*\*[^\|]*\|([^\|]+)/],
  control_system: [/数控系统[：:]\s*([^|，。\n]+)/, /\*\*数控系统\*\*[^\|]*\|([^\|]+)/],
  fixture: [/夹具名称[：:]\s*([^|，。\n]+)/, /\*\*夹具名称\*\*[^\|]*\|([^\|]+)/, /[-]\s*夹具名称[：:]\s*([^|，。\n]+)/],
  material: [/材料名称[：:]\s*([^|，。\n]+)/, /\*\*材料名称\*\*[^\|]*\|([^\|]+)/],
  tool_name: [/刀具名称[：:]\s*([^|，。\n]+)/, /名称[：:]\s*([^|<br>]+)/, /\*\*刀具\*\*[^\|]*\|([^\|]+)/],
  tool_length: [/长度[：:]\s*([^|，。\nmm]+)/, /\*\*长度\*\*[^\|]*\|([^\|]+)/],
  tool_diameter: [/直径[：:]\s*([^|，。\nmm]+)/, /\*\*直径\*\*[^\|]*\|([^\|]+)/]
}

const parseParameters = (text) => {
  const result = {}
  
  for (const field of REQUIRED_FIELDS) {
    result[field] = ''
    const patterns = fieldPatterns[field] || []
    
    for (const pattern of patterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const value = match[1].trim()
        if (value && (!result[field] || value.length > result[field].length)) {
          result[field] = value
        }
      }
    }
  }
  
  return result
}

const extractedParams = computed(() => {
  return parseParameters(inputText.value)
})

const filledFields = computed(() => {
  return REQUIRED_FIELDS.filter(field => {
    const value = extractedParams.value[field]
    return value && String(value).trim() !== ''
  })
})

const missingFields = computed(() => {
  return REQUIRED_FIELDS.filter(field => {
    const value = extractedParams.value[field]
    return !value || String(value).trim() === ''
  })
})

const handleInput = () => {
  // 只需要更新 inputText，computed 会自动处理参数解析
}

const handleConvert = async () => {
  loading.value = true
  
  try {
    console.log('正在转换...', inputText.value)
    const response = await naturalLanguageApi.convert(inputText.value)
    console.log('转换响应:', response)
    
    if (response.data.success) {
      console.log('转换成功，数据:', response.data.data)
      emit('convert', response.data.data)
    } else {
      console.log('参数不完整，缺失字段:', response.data.missing_fields)
    }
  } catch (error) {
    console.error('转换失败:', error)
    alert('转换失败，请检查输入内容')
  } finally {
    loading.value = false
  }
}

const handleClear = () => {
  inputText.value = ''
}
</script>