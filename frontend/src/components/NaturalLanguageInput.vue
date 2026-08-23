<template>
  <div class="bg-white rounded-xl shadow-lg p-6">
    <h2 class="text-xl font-bold text-gray-800 mb-2">自然语言转换</h2>
    <p class="text-sm text-gray-500 mb-6">请分次补充工序卡信息。信息完整后，先确认工序卡，再生成待审核 G 代码。</p>

    <div class="mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">本轮补充内容</label>
      <textarea
        v-model="inputText"
        rows="10"
        @input="handleInput"
        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none transition-all"
        placeholder="例如：\n产品名称：底板\n工序名称：键槽加工\n工序编号：02\n版本号：A\n设备：立式加工中心（发那科MD）\n数控系统：FANUC-0iM\n夹具：平口钳装夹\n材料：铝合金6061\n刀具名称：键槽铣刀，长度：50mm，直径：8mm\n冷却方式：油冷\n1. 粗铣键槽，刀具：键槽铣刀，X=0, Y=0, Z=2, F=200，工艺说明：每层切深2mm"
      ></textarea>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="p-4 bg-green-50 border border-green-200 rounded-lg">
        <h3 class="text-sm font-medium text-green-800 mb-2">已识别字段</h3>
        <ul class="space-y-1">
          <li v-for="field in filledFields" :key="field" class="text-sm text-green-700">- {{ fieldMap[field] || field }}</li>
          <li v-if="filledFields.length === 0" class="text-sm text-green-400 italic">暂无已识别字段</li>
        </ul>
      </div>

      <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
        <h3 class="text-sm font-medium text-red-800 mb-2">需要补充</h3>
        <ul class="space-y-1">
          <li v-for="field in missingFields" :key="field.path" class="text-sm text-red-700">
            - {{ field.label }}：{{ field.reason }}
          </li>
          <li v-if="missingFields.length === 0" class="text-sm text-red-400 italic">当前没有缺项</li>
        </ul>
      </div>
    </div>

    <div v-if="errorMessage" class="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
      {{ errorMessage }}
    </div>
    <div v-if="statusMessage" class="mb-4 p-3 bg-blue-50 border border-blue-200 text-blue-700 rounded-lg text-sm">
      {{ statusMessage }}
    </div>

    <div class="flex space-x-4">
      <button
        @click="submitDraft"
        :disabled="loading || !inputText.trim()"
        class="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      >
        {{ loading ? '检查中...' : '提交并检查工序卡' }}
      </button>
      <button
        @click="handleClear"
        :disabled="loading"
        class="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 disabled:opacity-50 transition-all"
      >
        清空
      </button>
    </div>

    <ProcessCardModal
      v-if="showConfirmation && draft"
      :process-card="draft.process_card"
      :operations="draft.operations"
      :field-sources="draft.field_sources"
      :confirming="confirming"
      @close="returnToInput"
      @back="returnToInput"
      @confirm="confirmDraft"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { naturalLanguageApi } from '../api'
import ProcessCardModal from './ProcessCardModal.vue'

const emit = defineEmits(['convert'])

const inputText = ref('')
const loading = ref(false)
const confirming = ref(false)
const statusMessage = ref('')
const errorMessage = ref('')
const filledFields = ref([])
const missingFields = ref([])
const draft = ref(null)
const revision = ref(0)
const digest = ref('')
const showConfirmation = ref(false)
const fieldMap = {
  product_name: '产品名称', process_name: '工序名称', process_number: '工序编号', version: '版本号',
  equipment: '设备名称', control_system: '数控系统', fixture: '夹具名称', material: '材料名称',
  tool_name: '刀具名称', tool_length: '刀具长度', tool_diameter: '刀具直径', cutting_fluid: '冷却方式', operations: '操作步骤'
}

const submitDraft = async () => {
  if (!inputText.value.trim() || loading.value) return
  loading.value = true
  errorMessage.value = ''
  statusMessage.value = ''
  showConfirmation.value = false
  try {
    const response = await naturalLanguageApi.precheck(inputText.value, draft.value, revision.value, digest.value)
    const data = response.data
    draft.value = data.draft
    revision.value = data.revision
    digest.value = data.digest
    filledFields.value = data.filled_fields || []
    missingFields.value = data.missing_fields || []
    statusMessage.value = data.message || ''
    inputText.value = ''
    sessionStorage.setItem('natural-language-draft', JSON.stringify({ draft: draft.value, revision: revision.value, digest: digest.value }))
    if (data.status === 'ready_for_confirmation') showConfirmation.value = true
  } catch (error) {
    errorMessage.value = error.response?.data?.detail?.message || error.response?.data?.detail || '工序卡检查失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const confirmDraft = async () => {
  if (!draft.value || confirming.value) return
  confirming.value = true
  errorMessage.value = ''
  try {
    const response = await naturalLanguageApi.confirm(draft.value, revision.value, digest.value)
    if (response.data.success && response.data.data) {
      showConfirmation.value = false
      emit('convert', response.data.data)
      sessionStorage.removeItem('natural-language-draft')
      statusMessage.value = 'G代码已生成，请完成规则审核和人工上机前检查。'
    } else {
      errorMessage.value = response.data.message || 'G代码未生成'
    }
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '确认生成失败，请重新检查工序卡'
  } finally {
    confirming.value = false
  }
}

const returnToInput = () => {
  showConfirmation.value = false
  statusMessage.value = '请补充或修改信息后重新提交。'
}

const handleInput = () => {
  showConfirmation.value = false
  statusMessage.value = ''
}

const handleClear = () => {
  inputText.value = ''
  draft.value = null
  revision.value = 0
  digest.value = ''
  filledFields.value = []
  missingFields.value = []
  statusMessage.value = ''
  errorMessage.value = ''
  showConfirmation.value = false
  sessionStorage.removeItem('natural-language-draft')
}
</script>
