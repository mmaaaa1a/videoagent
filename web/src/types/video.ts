// 视频处理相关的类型定义

export interface VideoProcessingItem {
  id: string
  name: string
  path: string
  size: number
  duration?: number
  thumbnail?: string
  status: 'pending' | 'processing' | 'completed' | 'error' | 'skipped'
  currentStage?: string
  progress: number // 0-100
  startTime?: Date
  completedTime?: Date
  error?: string
  retryCount?: number
  file?: File
}

export interface BatchProcessingState {
  totalVideos: number
  completedVideos: number
  failedVideos: number
  currentProcessingVideo?: string
  overallProgress: number // 0-100
  status: 'uploading' | 'processing' | 'completed' | 'error' | 'paused'
  estimatedTimeRemaining?: number // 秒
  startTime?: Date
  endTime?: Date
  videos: VideoProcessingItem[]
  averageProcessingTime?: number // 秒
}

export interface ProcessingStage {
  key: string
  label: string
  icon: string
  description: string
  weight: number // 用于计算进度权重
}

export const PROCESSING_STAGES: ProcessingStage[] = [
  { key: 'Starting Video', label: '开始处理', icon: '🎬', description: '初始化视频处理任务', weight: 5 },
  { key: 'Splitting Video', label: '分割视频', icon: '✂️', description: '将视频分割为小片段', weight: 15 },
  { key: 'Transcribing Audio', label: '语音转录', icon: '🎤', description: '提取音频并转录为文字', weight: 30 },
  { key: 'Processing Segments', label: '处理片段', icon: '⚙️', description: '分析视频片段内容', weight: 25 },
  { key: 'Encoding Features', label: '编码特征', icon: '🔮', description: '提取视频特征向量', weight: 20 },
  { key: 'One Video Completed', label: '视频完成', icon: '✅', description: '单个视频处理完成', weight: 5 },
]

export interface BatchSessionStatus {
  success: boolean
  chat_id: string
  status: 'processing' | 'completed' | 'error' | 'terminated'
  message: string
  current_step: string
  total_videos?: number
  completed_videos?: number
  indexed_videos?: string[]
  current_video?: string
  video_details?: {
    [video_name: string]: {
      status: string
      stage?: string
      progress: number
      error?: string
      start_time?: string
      completed_time?: string
    }
  }
  error?: string
}

export interface FileWithPath {
  file: File
  path: string
  relativePath: string
}

export interface VideoFile {
  id: string
  file: File
  name: string
  size: number
  status: 'valid' | 'invalid' | 'checking'
  thumbnail?: string
  duration?: number
  relativePath?: string
  error?: string
  retryCount?: number
}

export interface FolderUploadResult {
  files: FileWithPath[]
  totalCount: number
  totalSize: number
  videoCount: number
  directoryCount: number
  skippedCount: number
}

export interface ProcessingStats {
  totalProcessed: number
  successCount: number
  errorCount: number
  averageTimePerVideo: number
  totalProcessingTime: number
  successRate: number
}

export interface VideoProcessingProgress {
  stage: string
  message: string
  timestamp: Date
  videoId?: string
}

export interface BatchProcessingConfig {
  maxConcurrentProcessing: number
  retryOnError: boolean
  maxRetries: number
  showNotifications: boolean
  autoStartProcessing: boolean
}

export const DEFAULT_BATCH_CONFIG: BatchProcessingConfig = {
  maxConcurrentProcessing: 3,
  retryOnError: true,
  maxRetries: 2,
  showNotifications: true,
  autoStartProcessing: true,
}

// 工具函数
export function calculateStageProgress(currentStage: string): number {
  const stageIndex = PROCESSING_STAGES.findIndex(stage => stage.key === currentStage)
  if (stageIndex === -1) return 0

  let totalWeight = 0
  let completedWeight = 0

  for (let i = 0; i < PROCESSING_STAGES.length; i++) {
    totalWeight += PROCESSING_STAGES[i].weight
    if (i < stageIndex) {
      completedWeight += PROCESSING_STAGES[i].weight
    }
  }

  return Math.round((completedWeight / totalWeight) * 100)
}

export function getStageByKey(key: string): ProcessingStage | undefined {
  return PROCESSING_STAGES.find(stage => stage.key === key)
}

export function formatProcessingTime(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}秒`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.round(seconds % 60)
    return `${minutes}分${remainingSeconds}秒`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}小时${minutes}分钟`
  }
}

export function estimateRemainingTime(
  completedVideos: number,
  totalVideos: number,
  elapsedTime: number
): number {
  if (completedVideos === 0 || totalVideos === 0) return 0

  const averageTimePerVideo = elapsedTime / completedVideos
  const remainingVideos = totalVideos - completedVideos
  return Math.round(averageTimePerVideo * remainingVideos)
}

export function calculateSuccessRate(completed: number, failed: number): number {
  const total = completed + failed
  if (total === 0) return 0
  return Math.round((completed / total) * 100)
}