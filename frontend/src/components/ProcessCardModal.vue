<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b bg-green-50">
        <h2 class="text-xl font-bold text-green-800">工序卡信息</h2>
        <button @click="close" class="text-gray-500 hover:text-gray-700">
          <svg class="w-6 h-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="flex-1 overflow-auto p-4 max-h-[60vh]">
        <div class="mb-6">
          <h4 class="font-semibold text-gray-700 mb-3">基本信息</h4>
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div class="p-3 bg-gray-50 rounded-lg">
              <p class="text-gray-500">产品名称</p>
              <p class="font-medium">{{ processCard?.product_name }}</p>
            </div>
            <div class="p-3 bg-gray-50 rounded-lg">
              <p class="text-gray-500">工序名称</p>
              <p class="font-medium">{{ processCard?.process_name }}</p>
            </div>
            <div class="p-3 bg-gray-50 rounded-lg">
              <p class="text-gray-500">工序编号</p>
              <p class="font-medium">{{ processCard?.process_number }}</p>
            </div>
            <div class="p-3 bg-gray-50 rounded-lg">
              <p class="text-gray-500">版本号</p>
              <p class="font-medium">{{ processCard?.version }}</p>
            </div>
            <div class="p-3 bg-gray-50 rounded-lg">
              <p class="text-gray-500">设备名称</p>
              <p class="font-medium">{{ processCard?.equipment }}</p>
            </div>
            <div class="p-3 bg-gray-50 rounded-lg">
              <p class="text-gray-500">数控系统</p>
              <p class="font-medium">{{ processCard?.control_system }}</p>
            </div>
            <div class="p-3 bg-gray-50 rounded-lg">
              <p class="text-gray-500">夹具名称</p>
              <p class="font-medium">{{ processCard?.fixture }}</p>
            </div>
            <div class="p-3 bg-gray-50 rounded-lg">
              <p class="text-gray-500">材料名称</p>
              <p class="font-medium">{{ processCard?.material }}</p>
            </div>
          </div>
        </div>

        <div class="mb-6">
          <h4 class="font-semibold text-gray-700 mb-3">刀具信息</h4>
          <div class="p-3 bg-blue-50 rounded-lg">
            <div class="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p class="text-gray-500">刀具名称</p>
                <p class="font-medium">{{ processCard?.tool_info?.name }}</p>
              </div>
              <div>
                <p class="text-gray-500">长度(mm)</p>
                <p class="font-medium">{{ processCard?.tool_info?.length }}</p>
              </div>
              <div>
                <p class="text-gray-500">直径(mm)</p>
                <p class="font-medium">{{ processCard?.tool_info?.diameter }}</p>
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
              <tr v-for="op in operations" :key="op.sequence" class="border-t">
                <td class="px-3 py-2">{{ op.sequence }}</td>
                <td class="px-3 py-2">{{ op.content }}</td>
                <td class="px-3 py-2">{{ op.parameters }}</td>
                <td class="px-3 py-2">{{ op.equipment }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="p-4 border-t bg-gray-50">
        <button
          @click="close"
          class="w-full py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
        >
          关闭
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  processCard: {
    type: Object,
    required: true
  },
  operations: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close'])

const close = () => {
  emit('close')
}
</script>