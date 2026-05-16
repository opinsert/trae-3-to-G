import axios from 'axios'

const API_BASE_URL = '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000
})

export const naturalLanguageApi = {
  convert: (text) => api.post('/natural-language/convert', { text }),
  precheck: (text) => api.post('/natural-language/precheck', { text })
}

export const drawingApi = {
  convert: (processCard, operations) => api.post('/drawing/convert', { process_card: processCard, operations }),
  ocrExtract: (image) => api.post('/drawing/ocr-extract', { image })
}

export const stlApi = {
  convert: (stlFile, processCard) => api.post('/stl/convert', { stl_file: stlFile, process_card: processCard })
}

export const gcodeApi = {
  validate: (gcode, processCard) => api.post('/gcode/validate', { gcode, processCard })
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