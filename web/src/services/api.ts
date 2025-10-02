import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:64451'

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export interface VideoRAGConfig {
  openai_api_key: string
  openai_base_url?: string
  ali_dashscope_api_key: string
  ali_dashscope_base_url?: string
  analysisModel: string
  processingModel: string
  caption_model: string
  asr_model: string
  image_bind_model_path: string
  base_storage_path: string
}

export interface VideoDurationInfo {
  success: boolean
  duration: number
  fps: number
  width: number
  height: number
  video_path: string
  error?: string
}

export interface InitializeResponse {
  success: boolean
  message: string
  imagebind_status: any
  error?: string
}

export interface UploadResponse {
  success: boolean
  message: string
  video_names: string[]
  video_count: number
  chat_id: string
  status: string
  error?: string
}

export interface SessionStatus {
  success: boolean
  chat_id: string
  status: 'processing' | 'completed' | 'error' | 'terminated'
  message: string
  current_step: string
  query?: string
  answer?: string
  error?: string
}

export interface IndexedVideos {
  success: boolean
  indexed_videos: string[]
  total_count: number
  chat_id: string
  error?: string
}

export interface QueryResponse {
  success: boolean
  query: string
  message: string
  chat_id: string
  status: string
  error?: string
}

export interface SystemStatus {
  success: boolean
  global_config_set: boolean
  imagebind_initialized: boolean
  imagebind_loaded: boolean
  total_sessions: number
  total_indexed_videos: number
  running_processes: any
  sessions: string[]
  error?: string
}

// API Functions
export const videoRAGApi = {
  // Health check
  healthCheck: () => api.get('/api/health'),

  // Get video duration
  getVideoDuration: (videoPath: string) =>
    api.post<VideoDurationInfo>('/api/video/duration', { video_path: videoPath }),

  // Initialize system
  initializeSystem: (config: VideoRAGConfig) =>
    api.post<InitializeResponse>('/api/initialize', config),

  // Upload videos
  uploadVideos: (chatId: string, videoPathList: string[]) =>
    api.post<UploadResponse>(`/api/sessions/${chatId}/videos/upload`, {
      video_path_list: videoPathList,
    }),

  // Get session status
  getSessionStatus: (chatId: string, type: 'indexing' | 'query' = 'indexing') =>
    api.get<SessionStatus>(`/api/sessions/${chatId}/status?type=${type}`),

  // Get indexed videos
  getIndexedVideos: (chatId: string) =>
    api.get<IndexedVideos>(`/api/sessions/${chatId}/videos/indexed`),

  // Terminate session
  terminateSession: (chatId: string) =>
    api.post(`/api/sessions/${chatId}/terminate`),

  // Delete session
  deleteSession: (chatId: string) =>
    api.delete(`/api/sessions/${chatId}/delete`),

  // Query video
  queryVideo: (chatId: string, query: string) =>
    api.post<QueryResponse>(`/api/sessions/${chatId}/query`, { query }),

  // Get system status
  getSystemStatus: () => api.get<SystemStatus>('/api/system/status'),

  // Get ImageBind status
  getImageBindStatus: () => api.get('/api/imagebind/status'),

  // Load ImageBind model
  loadImageBind: () => api.post('/api/imagebind/load'),

  // Release ImageBind model
  releaseImageBind: () => api.post('/api/imagebind/release'),
}