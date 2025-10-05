import axios from 'axios'

// 动态检测当前访问地址，支持localhost和IP地址
const getApiBaseUrl = () => {
  // 如果有环境变量配置，优先使用
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }

  // 生产环境使用相对路径
  if (import.meta.env.PROD) {
    return ''
  }

  // 开发环境自动检测当前访问地址
  const currentHost = window.location.hostname
  const apiPort = import.meta.env.VITE_API_PORT || 64451

  // 如果是localhost，使用localhost
  if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
    return `http://localhost:${apiPort}`
  }

  // 如果是IP地址，使用相同的IP
  if (/^\d+\.\d+\.\d+\.\d+$/.test(currentHost)) {
    return `http://${currentHost}:${apiPort}`
  }

  // 其他情况使用默认配置
  return `http://localhost:${apiPort}`
}

const API_BASE_URL = getApiBaseUrl()

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
  asr_mode: string  // 'local' 或 'api'
  asr_model: string // local模式: large-v3等，api模式: paraformer-realtime-v2等
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

export interface VideoItem {
  type: 'file' | 'directory'
  name: string
  path: string
  relative_path?: string
  size?: number
  size_mb?: number
  modified: number
  format?: string
  children?: VideoItem[]
  total_files?: number
  total_size?: number
  total_size_mb?: number
  expanded?: boolean
  selected?: boolean
}

export interface AvailableVideosResponse {
  success: boolean
  structure: {
    base_path: string
    items: VideoItem[]
    total_items: number
  }
  error?: string
}

export interface DefaultConfigResponse {
  success: boolean
  defaults: {
    openai_base_url: string
    openai_api_key: string
    processing_model: string
    analysis_model: string
    dashscope_api_key: string
    dashscope_base_url: string
    caption_model: string
    asr_model: string
    store_directory: string
    imagebind_model_directory: string
    selected_imagebind_model: string
  }
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
  // Update system configuration
  updateSystemConfig: (config: VideoRAGConfig) =>
    api.post<InitializeResponse>('/api/config/update', config),

  // Get available videos for selection
  getAvailableVideos: () =>
    api.get<AvailableVideosResponse>('/api/videos/available'),

  // Upload videos
  uploadVideos: (chatId: string, videoPathList: string[]) =>
    api.post<UploadResponse>(`/api/sessions/${chatId}/videos/upload`, {
      video_path_list: videoPathList,
    }),

  // Upload videos via web interface (for file picker results)
  uploadVideosWeb: (chatId: string, selectedFiles: string[]) =>
    api.post<UploadResponse>(`/api/sessions/${chatId}/videos/upload-web`, {
      uploaded_files: selectedFiles.map(path => ({ file_path: path }))
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

  // Get VideoRAG default configuration
  getDefaultConfig: () => api.get<DefaultConfigResponse>('/api/videorag/defaults'),
}