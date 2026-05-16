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
      <label class="block text-sm font-medium text-gray-700 mb-2">操作步骤</label>
      <div class="space-y-3">
        <div v-for="(op, index) in form.operations" :key="index" class="flex items-center gap-3">
          <span class="w-8 h-8 flex items-center justify-center bg-blue-100 text-blue-600 rounded-full text-sm font-medium">{{ index + 1 }}</span>
          <input v-model="op.content" type="text" placeholder="操作内容" class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          <input v-model="op.parameters" type="text" placeholder="工艺参数（如 X=0, Y=0, Z=50）" class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          <button @click="removeOperation(index)" class="px-3 py-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors">
            <svg class="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      <button @click="addOperation" class="mt-3 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
        + 添加步骤
      </button>
    </div>

    <div v-if="missingFields.length > 0" class="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
      <p class="text-yellow-800 font-medium">请补充以下缺失的参数：</p>
      <ul class="mt-2 space-y-1">
        <li v-for="field in missingFields" :key="field" class="text-yellow-700">- {{ field }}</li>
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
import { ref, reactive } from 'vue'
import { drawingApi } from '../api'

const emit = defineEmits(['convert'])

const fileInput = ref(null)
const uploadedImage = ref('')
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
  },
  operations: [
    { sequence: 1, content: '', parameters: '', equipment: '', remark: '' },
    { sequence: 2, content: '', parameters: '', equipment: '', remark: '' }
  ]
})

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      uploadedImage.value = e.target?.result
    }
    reader.readAsDataURL(file)
  }
}

const handleDrop = (event) => {
  const file = event.dataTransfer?.files?.[0]
  if (file && file.type.startsWith('image/')) {
    const reader = new FileReader()
    reader.onload = (e) => {
      uploadedImage.value = e.target?.result
    }
    reader.readAsDataURL(file)
  }
}

const addOperation = () => {
  form.operations.push({
    sequence: form.operations.length + 1,
    content: '',
    parameters: '',
    equipment: '',
    remark: ''
  })
}

const removeOperation = (index) => {
  if (form.operations.length > 1) {
    form.operations.splice(index, 1)
    form.operations.forEach((op, i) => {
      op.sequence = i + 1
    })
  }
}

const convert = async () => {
  loading.value = true
  missingFields.value = []
  
  try {
    const response = await drawingApi.convert(form, form.operations)
    
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
</script>
