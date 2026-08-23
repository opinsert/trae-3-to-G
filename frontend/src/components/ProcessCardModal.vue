<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden">
      <div class="flex items-center justify-between px-6 py-4 border-b bg-green-50">
        <div>
          <h2 class="text-xl font-bold text-green-800">请确认工序卡</h2>
          <p class="text-xs text-green-700 mt-1">确认前不会生成 G 代码；确认后仍需人工审核、仿真、空运行和试切。</p>
        </div>
        <button @click="back" class="text-gray-500 hover:text-gray-700">返回补充</button>
      </div>

      <div class="overflow-auto p-6 max-h-[72vh]">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm mb-6">
          <div v-for="field in cardFields" :key="field.key" class="p-3 bg-gray-50 rounded-lg">
            <p class="text-gray-500">{{ field.label }}</p>
            <p class="font-medium">{{ processCard?.[field.key] || '—' }}</p>
          </div>
        </div>

        <div class="p-4 bg-blue-50 rounded-lg mb-6">
          <h4 class="font-semibold text-gray-700 mb-3">刀具与冷却</h4>
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
            <div><p class="text-gray-500">刀具名称</p><p class="font-medium">{{ processCard?.tool_info?.name || '—' }}</p></div>
            <div><p class="text-gray-500">长度(mm)</p><p class="font-medium">{{ processCard?.tool_info?.length || '—' }}</p></div>
            <div><p class="text-gray-500">直径(mm)</p><p class="font-medium">{{ processCard?.tool_info?.diameter || '—' }}</p></div>
            <div><p class="text-gray-500">冷却方式</p><p class="font-medium">{{ processCard?.cutting_fluid || '—' }}</p></div>
          </div>
        </div>

        <div>
          <h4 class="font-semibold text-gray-700 mb-3">操作步骤</h4>
          <table class="w-full text-sm border-collapse">
            <thead>
              <tr class="bg-gray-100">
                <th class="px-3 py-2 text-left">序号</th>
                <th class="px-3 py-2 text-left">操作内容</th>
                <th class="px-3 py-2 text-left">工艺参数/要求</th>
                <th class="px-3 py-2 text-left">刀具</th>
                <th class="px-3 py-2 text-left">工艺说明</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="op in operations" :key="op.sequence" class="border-t">
                <td class="px-3 py-2">{{ op.sequence }}</td>
                <td class="px-3 py-2">{{ op.content }}</td>
                <td class="px-3 py-2">{{ op.parameters }}</td>
                <td class="px-3 py-2">{{ op.equipment }}</td>
                <td class="px-3 py-2">{{ op.remark }}</td>
              </tr>
              <tr v-if="operations.length === 0" class="border-t">
                <td colspan="5" class="px-3 py-4 text-center text-gray-500">暂无操作步骤</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="p-4 border-t bg-gray-50 flex gap-4">
        <button @click="back" class="flex-1 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">返回补充</button>
        <button @click="confirm" :disabled="confirming" class="flex-1 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50">
          {{ confirming ? '生成中...' : '确认并生成 G 代码' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  processCard: { type: Object, required: true },
  operations: { type: Array, default: () => [] },
  fieldSources: { type: Object, default: () => ({}) },
  confirming: { type: Boolean, default: false }
})

const emit = defineEmits(['close', 'back', 'confirm'])
const cardFields = [
  { key: 'product_name', label: '产品名称' },
  { key: 'process_name', label: '工序名称' },
  { key: 'process_number', label: '工序编号' },
  { key: 'version', label: '版本号' },
  { key: 'equipment', label: '设备名称' },
  { key: 'control_system', label: '数控系统' },
  { key: 'fixture', label: '夹具名称' },
  { key: 'material', label: '材料名称' }
]
const back = () => emit('back')
const confirm = () => emit('confirm')
</script>
