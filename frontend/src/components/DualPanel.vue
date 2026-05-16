<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b bg-gray-50">
        <h2 class="text-xl font-bold text-gray-800">G代码转换结果</h2>
        <button @click="close" class="text-gray-500 hover:text-gray-700">
          <svg class="w-6 h-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="flex h-[calc(90vh-64px)]">
        <div class="flex-1 border-r border-gray-200 flex flex-col">
          <div class="px-4 py-3 bg-blue-50 border-b">
            <h3 class="font-medium text-blue-800">G代码</h3>
          </div>
          <div class="flex-1 overflow-auto p-4">
            <pre class="gcode-textarea whitespace-pre-wrap text-sm"><code>{{ data.gcode }}</code></pre>
          </div>
          <div class="p-4 border-t bg-gray-50">
            <button
              @click="copyGCode"
              class="w-full py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              {{ copied ? '已复制!' : '复制G代码' }}
            </button>
          </div>
        </div>

        <div class="flex-1 flex flex-col">
          <div class="px-4 py-3 bg-green-50 border-b">
            <h3 class="font-medium text-green-800">工序卡信息</h3>
          </div>
          <div class="flex-1 overflow-auto p-4">
            <div class="mb-6">
              <h4 class="font-semibold text-gray-700 mb-3">基本信息</h4>
              <div class="grid grid-cols-2 gap-3 text-sm">
                <div class="p-3 bg-gray-50 rounded-lg">
                  <p class="text-gray-500">产品名称</p>
                  <p class="font-medium">{{ data.process_card?.product_name }}</p>
                </div>
                <div class="p-3 bg-gray-50 rounded-lg">
                  <p class="text-gray-500">工序名称</p>
                  <p class="font-medium">{{ data.process_card?.process_name }}</p>
                </div>
                <div class="p-3 bg-gray-50 rounded-lg">
                  <p class="text-gray-500">工序编号</p>
                  <p class="font-medium">{{ data.process_card?.process_number }}</p>
                </div>
                <div class="p-3 bg-gray-50 rounded-lg">
                  <p class="text-gray-500">版本号</p>
                  <p class="font-medium">{{ data.process_card?.version }}</p>
                </div>
                <div class="p-3 bg-gray-50 rounded-lg">
                  <p class="text-gray-500">设备名称</p>
                  <p class="font-medium">{{ data.process_card?.equipment }}</p>
                </div>
                <div class="p-3 bg-gray-50 rounded-lg">
                  <p class="text-gray-500">数控系统</p>
                  <p class="font-medium">{{ data.process_card?.control_system }}</p>
                </div>
                <div class="p-3 bg-gray-50 rounded-lg">
                  <p class="text-gray-500">夹具名称</p>
                  <p class="font-medium">{{ data.process_card?.fixture }}</p>
                </div>
                <div class="p-3 bg-gray-50 rounded-lg">
                  <p class="text-gray-500">材料名称</p>
                  <p class="font-medium">{{ data.process_card?.material }}</p>
                </div>
              </div>
            </div>

            <div class="mb-6">
              <h4 class="font-semibold text-gray-700 mb-3">刀具信息</h4>
              <div class="p-3 bg-blue-50 rounded-lg">
                <div class="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p class="text-gray-500">刀具名称</p>
                    <p class="font-medium">{{ data.process_card?.tool_info?.name }}</p>
                  </div>
                  <div>
                    <p class="text-gray-500">长度(mm)</p>
                    <p class="font-medium">{{ data.process_card?.tool_info?.length }}</p>
                  </div>
                  <div>
                    <p class="text-gray-500">直径(mm)</p>
                    <p class="font-medium">{{ data.process_card?.tool_info?.diameter }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h4 class="font-semibold text-gray-700 mb-3">操作步骤</h4>
              <table class="w-full text-sm border-collapse">
                <thead>
                  <tr class="bg-gray-100">
                    <th class="px-3 py-2 text-left font-medium">序号</th>
                    <th class="px-3 py-2 text-left font-medium">操作内容</th>
                    <th class="px-3 py-2 text-left font-medium">工艺参数</th>
                    <th class="px-3 py-2 text-left font-medium">设备/工具</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="op in data.operations" :key="op.sequence" class="border-t">
                    <td class="px-3 py-2">{{ op.sequence }}</td>
                    <td class="px-3 py-2">{{ op.content }}</td>
                    <td class="px-3 py-2">{{ op.parameters }}</td>
                    <td class="px-3 py-2">{{ op.equipment }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div v-if="data.validation" class="px-6 py-4 border-t bg-gray-50">
        <div class="flex items-center gap-4">
          <div :class="[
            'px-4 py-2 rounded-full text-sm font-medium',
            data.validation.valid ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          ]">
            {{ data.validation.valid ? '✓ 验证通过' : '✗ 验证失败' }}
          </div>
          <div v-if="data.validation.errors.length > 0" class="text-red-600 text-sm">
            发现 {{ data.validation.errors.length }} 个错误
          </div>
          <div v-if="data.validation.warnings.length > 0" class="text-yellow-600 text-sm">
            发现 {{ data.validation.warnings.length }} 个警告
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  data: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close'])

const copied = ref(false)

const close = () => {
  emit('close')
}

const copyGCode = async () => {
  try {
    await navigator.clipboard.writeText(props.data.gcode)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (error) {
    console.error('复制失败:', error)
  }
}
</script>
