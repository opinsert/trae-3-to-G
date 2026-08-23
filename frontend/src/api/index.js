import axios from 'axios'

const API_BASE_URL = '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000
})

export const naturalLanguageApi = {
  precheck: (message, draft = null, revision = 0, digest = '') => api.post('/natural-language/precheck', {
    message,
    draft,
    revision,
    digest
  }),
  confirm: (draft, revision, digest) => api.post('/natural-language/confirm', {
    confirmed: true,
    draft,
    revision,
    digest
  })
}

export const drawingApi = {
  convert: (processCard, steps) => api.post('/drawing/convert', { process_card: processCard, steps }),
  ocrExtract: (image) => api.post('/drawing/ocr-extract', { image })
}

export const stlApi = {
  convert: (stlFile, processCard, direction = '+Z') => api.post('/stl/convert', { stl_file: stlFile, process_card: processCard, generate_gcode: false, direction }),
  generateGcode: (stlFile, processCard, operations, direction = '+Z') => api.post('/stl/convert', { stl_file: stlFile, process_card: processCard, operations, generate_gcode: true, direction }),
  planDirections: (stlFile, processCard) => api.post('/stl/plan-directions', { stl_file: stlFile, process_card: processCard }),
}

export const gcodeApi = {
  validate: (gcode, processCard = null) => api.post('/gcode/validate', { gcode, process_card: processCard })
}

export const examplesApi = {
  list: (category = null) => api.get('/examples', { params: { category } }),
  get: (id) => api.get(`/examples/${id}`),
  categories: () => api.get('/examples/categories')
}

export const advanceApi = {
  generateDrawing: (inputType, inputData, processCard) => 
    api.post('/advance/generate-drawing', { input_type: inputType, input_data: inputData, process_card: processCard })
}

export default api