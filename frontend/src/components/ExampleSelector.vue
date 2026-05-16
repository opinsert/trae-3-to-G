<template>
  <div class="bg-white rounded-xl shadow-lg p-6">
    <h2 class="text-xl font-bold text-gray-800 mb-6">工序卡示例</h2>
    
    <div class="flex flex-wrap gap-2 mb-6">
      <button
        @click="selectedCategory = null"
        :class="[
          'px-4 py-2 rounded-lg font-medium transition-all',
          !selectedCategory
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        ]"
      >
        全部
      </button>
      <button
        v-for="cat in categories"
        :key="cat"
        @click="selectedCategory = cat"
        :class="[
          'px-4 py-2 rounded-lg font-medium transition-all',
          selectedCategory === cat
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        ]"
      >
        {{ cat }}
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="example in filteredExamples"
        :key="example.id"
        @click="selectExample(example)"
        class="border border-gray-200 rounded-lg p-5 cursor-pointer hover:border-blue-500 hover:shadow-md transition-all group"
      >
        <div class="flex items-start justify-between mb-3">
          <h3 class="font-semibold text-gray-800 group-hover:text-blue-600 transition-colors">
            {{ example.name }}
          </h3>
          <span class="px-2 py-1 bg-blue-100 text-blue-600 text-xs rounded-full">
            {{ example.category }}
          </span>
        </div>
        <p class="text-sm text-gray-600 mb-3">{{ example.description }}</p>
        <div class="flex items-center justify-between text-xs text-gray-500">
          <span>产品: {{ example.card_data.product_name }}</span>
          <span>工序: {{ example.card_data.process_name }}</span>
        </div>
        <button class="mt-4 w-full py-2 border border-blue-500 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors">
          查看详情
        </button>
      </div>
    </div>

    <div v-if="selectedExample" class="mt-8 p-6 bg-blue-50 rounded-xl">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-bold text-gray-800">示例详情: {{ selectedExample.name }}</h3>
        <button @click="selectedExample = null" class="text-gray-500 hover:text-gray-700">
          <svg class="w-6 h-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h4 class="font-medium text-gray-700 mb-3">工序卡信息</h4>
          <div class="space-y-2 text-sm">
            <p><span class="text-gray-500">产品名称:</span> {{ selectedExample.card_data.product_name }}</p>
            <p><span class="text-gray-500">工序名称:</span> {{ selectedExample.card_data.process_name }}</p>
            <p><span class="text-gray-500">工序编号:</span> {{ selectedExample.card_data.process_number }}</p>
            <p><span class="text-gray-500">版本号:</span> {{ selectedExample.card_data.version }}</p>
            <p><span class="text-gray-500">设备:</span> {{ selectedExample.card_data.equipment }}</p>
            <p><span class="text-gray-500">数控系统:</span> {{ selectedExample.card_data.control_system }}</p>
            <p><span class="text-gray-500">刀具:</span> {{ selectedExample.card_data.tool_info.name }} (直径{{ selectedExample.card_data.tool_info.diameter }}mm)</p>
          </div>
        </div>
        
        <div>
          <h4 class="font-medium text-gray-700 mb-3">操作步骤</h4>
          <div class="space-y-2">
            <div v-for="op in selectedExample.operations_data" :key="op.sequence" class="p-3 bg-white rounded-lg border border-gray-100">
              <p class="font-medium text-blue-600">步骤 {{ op.sequence }}: {{ op.content }}</p>
              <p class="text-sm text-gray-600 mt-1">参数: {{ op.parameters }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <button
        @click="useExample"
        class="mt-6 w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
      >
        使用此示例生成G代码
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { examplesApi } from '../api'

const emit = defineEmits(['select'])

const examples = ref([])
const categories = ref([])
const selectedCategory = ref(null)
const selectedExample = ref(null)

const filteredExamples = computed(() => {
  if (!selectedCategory.value) {
    return examples.value
  }
  return examples.value.filter(ex => ex.category === selectedCategory.value)
})

const loadExamples = async () => {
  try {
    const response = await examplesApi.list()
    if (response.data.success) {
      examples.value = response.data.data
    }
  } catch (error) {
    console.error('加载示例失败:', error)
  }
}

const loadCategories = async () => {
  try {
    const response = await examplesApi.categories()
    if (response.data.success) {
      categories.value = response.data.data
    }
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

const selectExample = (example) => {
  selectedExample.value = example
}

const useExample = () => {
  if (selectedExample.value) {
    emit('select', selectedExample.value)
  }
}

onMounted(() => {
  loadExamples()
  loadCategories()
})
</script>
