<template>
  <div class="bg-white rounded-xl shadow-lg p-6">
    <h2 class="text-xl font-bold text-gray-800 mb-6">进阶功能</h2>
    
    <div class="mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">选择输入类型</label>
      <div class="flex space-x-4">
        <button
          v-for="type in inputTypes"
          :key="type.id"
          @click="selectedInputType = type.id"
          :class="[
            'flex-1 py-3 px-4 rounded-lg font-medium transition-all',
            selectedInputType === type.id
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          ]"
        >
          {{ type.name }}
        </button>
      </div>
    </div>

    <div v-if="selectedInputType === 'natural'" class="mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">输入自然语言指令</label>
      <textarea
        v-model="inputData"
        rows="6"
        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 resize-none"
        placeholder="请输入工序卡相关的自然语言描述..."
      ></textarea>
    </div>

    <div v-if="selectedInputType === 'stl'" class="mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">上传STL文件</label>
      <div
        @click="triggerStlUpload"
        @dragover.prevent
        @drop.prevent="handleStlDrop"
        class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 hover:bg-blue-50 cursor-pointer transition-all"
      >
        <input
          ref="stlFileInput"
          type="file"
          accept=".stl"
          @change="handleStlSelect"
          class="hidden"
        />
        <svg class="mx-auto h-12 w-12 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <p class="mt-2 text-sm text-gray-600">点击或拖拽上传STL文件</p>
        <p v-if="stlFileName" class="mt-2 text-sm text-blue-600">已选择: {{ stlFileName }}</p>
      </div>
    </div>

    <div class="mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">工序卡信息</label>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label class="block text-xs text-gray-500 mb-1">产品名称</label>
          <input v-model="form.product_name" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label class="block text-xs text-gray-500 mb-1">工序名称</label>
          <input v-model="form.process_name" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label class="block text-xs text-gray-500 mb-1">设备名称</label>
          <input v-model="form.equipment" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label class="block text-xs text-gray-500 mb-1">刀具名称</label>
          <input v-model="form.tool_info.name" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
        </div>
      </div>
    </div>

    <div class="flex space-x-4">
      <button
        @click="generate"
        :disabled="loading"
        class="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      >
        <span v-if="loading">生成中...</span>
        <span v-else>生成工序图和G代码</span>
      </button>
    </div>

    <div v-if="generatedDrawings.length > 0" class="mt-8">
      <h3 class="text-lg font-bold text-gray-800 mb-4">生成结果</h3>
      <div class="space-y-6">
        <div
          v-for="(item, index) in generatedDrawings"
          :key="index"
          class="border border-gray-200 rounded-xl p-4"
        >
          <div class="flex items-start justify-between mb-4">
            <h4 class="font-semibold text-gray-700">步骤 {{ item.step }}</h4>
            <span class="px-3 py-1 bg-blue-100 text-blue-600 text-sm rounded-full">
              {{ item.operation_content }}
            </span>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p class="text-sm text-gray-500 mb-2">工序图</p>
              <img :src="item.drawing" alt="工序图" class="max-w-full rounded-lg border border-gray-200" />
            </div>
            <div>
              <p class="text-sm text-gray-500 mb-2">G代码片段</p>
              <pre class="gcode-textarea bg-gray-100 p-3 rounded-lg text-sm whitespace-pre-wrap">{{ item.gcode_segment }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { advanceApi, naturalLanguageApi } from '../api'

const emit = defineEmits(['convert'])

const inputTypes = [
  { id: 'natural', name: '自然语言' },
  { id: 'stl', name: 'STL文件' }
]

const selectedInputType = ref('natural')
const inputData = ref('')
const stlFileInput = ref(null)
const stlFile = ref('')
const stlFileName = ref('')
const loading = ref(false)
const generatedDrawings = ref([])

const form = reactive({
  product_name: '',
  process_name: '',
  equipment: '',
  tool_info: {
    name: '',
    length: 0,
    diameter: 0
  }
})

const triggerStlUpload = () => {
  stlFileInput.value?.click()
}

const handleStlSelect = (event) => {
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

const handleStlDrop = (event) => {
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

const generate = async () => {
  loading.value = true
  generatedDrawings.value = []
  
  try {
    if (selectedInputType.value === 'natural' && inputData.value) {
      const response = await naturalLanguageApi.convert(inputData.value)
      if (response.data.success) {
        emit('convert', response.data.data)
      }
    } else {
      const response = await advanceApi.generateDrawing(
        selectedInputType.value,
        selectedInputType.value === 'stl' ? stlFile.value : inputData.value,
        form
      )
      
      if (response.data.success) {
        generatedDrawings.value = response.data.data.drawings || []
        
        if (generatedDrawings.value.length > 0) {
          const gcode = generatedDrawings.value.map(d => d.gcode_segment).join('\n\n')
          const mockData = {
            process_card: form,
            operations: generatedDrawings.value.map((d, i) => ({
              sequence: i + 1,
              content: d.operation_content,
              parameters: '',
              equipment: form.tool_info.name || 'CNC加工中心',
              remark: ''
            })),
            gcode: gcode,
            validation: { valid: true, errors: [], warnings: [] }
          }
          emit('convert', mockData)
        }
      }
    }
  } catch (error) {
    console.error('生成失败:', error)
    alert('生成失败')
  } finally {
    loading.value = false
  }
}
</script>
