<template>
  <div class="bg-white rounded-xl shadow-lg p-6">
    <h2 class="text-xl font-bold text-gray-800 mb-6">STL文件转换</h2>
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">上传STL文件</label>
        <div
          @click="triggerUpload"
          @dragover.prevent
          @drop.prevent="handleDrop"
          class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 hover:bg-blue-50 cursor-pointer transition-all"
        >
          <input
            ref="fileInput"
            type="file"
            accept=".stl"
            @change="handleFileSelect"
            class="hidden"
          />
          <svg class="mx-auto h-12 w-12 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p class="mt-2 text-sm text-gray-600">点击或拖拽上传STL文件</p>
          <p class="mt-1 text-xs text-gray-400">支持 .stl 格式</p>
        </div>
        
        <div v-if="stlFileName" class="mt-4 p-3 bg-gray-50 rounded-lg">
          <p class="text-sm text-gray-700">已选择: {{ stlFileName }}</p>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">填写工序卡信息</label>
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

    <div v-if="missingFields && missingFields.length > 0" class="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
      <p class="text-yellow-800 font-medium">请补充以下缺失的参数：</p>
      <ul class="mt-2 space-y-1">
        <template v-for="(field, index) in (missingFields || [])" :key="index">
          <li v-if="typeof field === 'string'" class="text-yellow-700">- {{ field }}</li>
        </template>
      </ul>
    </div>

    <div class="mt-6 flex space-x-4">
      <button
        @click="convert"
        :disabled="loading || !stlFile"
        class="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      >
        <span v-if="loading">转换中...</span>
        <span v-else>生成G代码</span>
      </button>
      
      <button
        @click="clear"
        class="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 focus:ring-4 focus:ring-gray-200 transition-all"
      >
        重置
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { stlApi } from '../api'

const emit = defineEmits(['convert'])

const fileInput = ref(null)
const stlFile = ref('')
const stlFileName = ref('')
const loading = ref(false)
const missingFields = ref([])

const form = reactive({
  product_name: '',
  process_name: '',
  process_number: '',
  version: '',
  equipment: '',
  control_system: '',
  fixture: '',
  material: '',
  tool_info: {
    name: '',
    length: 0,
    diameter: 0
  }
})

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (file) {
    stlFileName.value = file.name
    const reader = new FileReader()
    reader.onload = (e) => {
      stlFile.value = e.target?.result.split(',')[1] || ''
    }
    reader.readAsDataURL(file)
  }
}

const handleDrop = (event) => {
  const file = event.dataTransfer?.files?.[0]
  if (file && file.name.endsWith('.stl')) {
    stlFileName.value = file.name
    const reader = new FileReader()
    reader.onload = (e) => {
      stlFile.value = e.target?.result.split(',')[1] || ''
    }
    reader.readAsDataURL(file)
  }
}

const convert = async () => {
  loading.value = true
  missingFields.value = []
  
  try {
    const response = await stlApi.convert(stlFile.value, form)
    
    if (response.data.success) {
      emit('convert', response.data.data)
    } else {
      missingFields.value = response.data.missing_fields || []
    }
  } catch (error) {
    console.error('转换失败:', error)
    alert('转换失败')
  } finally {
    loading.value = false
  }
}

const clear = () => {
  stlFile.value = ''
  stlFileName.value = ''
  Object.keys(form).forEach(key => {
    if (key === 'tool_info') {
      form.tool_info = { name: '', length: 0, diameter: 0 }
    } else {
      form[key] = ''
    }
  })
  missingFields.value = []
}
</script>
