<template>
  <div class="min-h-screen bg-gray-100">
    <header class="bg-gradient-to-r from-blue-600 to-indigo-700 text-white shadow-lg">
      <div class="max-w-7xl mx-auto px-4 py-6">
        <h1 class="text-3xl font-bold">G代码转换系统</h1>
        <p class="mt-2 text-blue-100">将自然语言、工序图和STL文件转换为待审核的G代码</p>
        <p class="mt-2 text-xs text-yellow-100">仿真模式：所有长度使用 mm，进给使用 mm/min；验证通过仍需人工审核、空运行和试切后才能上机。</p>
      </div>
    </header>

    <nav class="bg-white border-b shadow-sm">
      <div class="max-w-7xl mx-auto px-4">
        <div class="flex space-x-1">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="switchTab(tab.id)"
            :class="[
              'px-6 py-4 font-medium transition-colors duration-200 border-b-2',
              currentTab === tab.id
                ? 'text-blue-600 border-blue-600 bg-blue-50'
                : 'text-gray-600 border-transparent hover:text-gray-900 hover:bg-gray-50'
            ]"
          >
            {{ tab.name }}
          </button>
        </div>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-4 py-6">
      <NaturalLanguageInput
        v-if="currentTab === 'natural'"
        @convert="handleConvert"
      />
      <DrawingUpload
        v-if="currentTab === 'drawing'"
        @convert="handleConvert"
      />
      <StlUpload
        v-if="currentTab === 'stl'"
        @convert="handleConvert"
      />
      <InlineGCodeViewer
        v-if="convertedData?.gcode && currentTab !== 'stl'"
        :gcode="convertedData.gcode"
        :validation="convertedData.validation"
      />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import NaturalLanguageInput from './components/NaturalLanguageInput.vue'
import DrawingUpload from './components/DrawingUpload.vue'
import StlUpload from './components/StlUpload.vue'
import InlineGCodeViewer from './components/InlineGCodeViewer.vue'

const tabs = [
  { id: 'natural', name: '自然语言转换' },
  { id: 'drawing', name: '工序图转换' },
  { id: 'stl', name: 'STL文件转换' }
]

const currentTab = ref('natural')
const convertedData = ref(null)

const switchTab = (tabId) => {
  currentTab.value = tabId
  convertedData.value = null
}

const handleConvert = (data) => {
  if (data) {
    convertedData.value = data
  } else {
    alert('转换失败：没有收到数据')
  }
}
</script>