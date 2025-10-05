import { useState, useEffect, useCallback, useRef } from 'react'
import { videoRAGApi } from '../services/api'
import {
  BatchProcessingState,
  VideoProcessingItem,
  BatchSessionStatus,
  ProcessingStage,
  PROCESSING_STAGES,
  getStageByKey,
  calculateStageProgress,
  estimateRemainingTime,
  formatProcessingTime
} from '../types/video'

interface UseBatchProcessingStatusOptions {
  chatId: string
  totalVideos: number
  initialVideos?: VideoProcessingItem[]
  onVideoCompleted?: (video: VideoProcessingItem) => void
  onBatchCompleted?: () => void
  onError?: (error: string) => void
  pollingInterval?: number
  enabled?: boolean
}

export function useBatchProcessingStatus({
  chatId,
  totalVideos,
  initialVideos = [],
  onVideoCompleted,
  onBatchCompleted,
  onError,
  pollingInterval = 2000, // 默认2秒轮询
  enabled = true
}: UseBatchProcessingStatusOptions) {
  const [batchState, setBatchState] = useState<BatchProcessingState>({
    totalVideos,
    completedVideos: 0,
    failedVideos: 0,
    overallProgress: 0,
    status: 'processing',
    videos: initialVideos,
  })

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<any>(null)
  const lastStatusRef = useRef<BatchSessionStatus | null>(null)

  // 将后端状态映射到前端状态
  const mapBackendStatusToFrontend = useCallback((
    backendStatus: BatchSessionStatus,
    currentBatchState: BatchProcessingState
  ): BatchProcessingState => {
    const completedVideos = backendStatus.indexed_videos?.length || 0
    const failedVideos = Object.values(backendStatus.video_details || {})
      .filter(detail => detail.status === 'error').length

    // 更新视频状态
    const updatedVideos = currentBatchState.videos.map(video => {
      const videoDetail = backendStatus.video_details?.[video.name]
      if (videoDetail) {
        const currentStage = getStageByKey(videoDetail.stage || '')
        const progress = videoDetail.stage ? calculateStageProgress(videoDetail.stage) : 0

        return {
          ...video,
          status: videoDetail.status as VideoProcessingItem['status'],
          currentStage: videoDetail.stage,
          progress,
          error: videoDetail.error,
          startTime: videoDetail.start_time ? new Date(videoDetail.start_time) : video.startTime,
          completedTime: videoDetail.completed_time ? new Date(videoDetail.completed_time) : video.completedTime,
        }
      }
      return video
    })

    // 计算整体进度
    const overallProgress = Math.round((completedVideos / currentBatchState.totalVideos) * 100)

    // 估算剩余时间
    const now = new Date()
    const elapsedTime = currentBatchState.startTime
      ? (now.getTime() - currentBatchState.startTime.getTime()) / 1000
      : 0
    const estimatedTimeRemaining = estimateRemainingTime(completedVideos, currentBatchState.totalVideos, elapsedTime)

    return {
      ...currentBatchState,
      completedVideos,
      failedVideos,
      overallProgress,
      status: backendStatus.status as BatchProcessingState['status'],
      currentProcessingVideo: backendStatus.current_video,
      videos: updatedVideos,
      estimatedTimeRemaining,
      endTime: backendStatus.status === 'completed' ? now : currentBatchState.endTime,
    }
  }, [])

  // 获取处理状态
  const fetchStatus = useCallback(async () => {
    if (!enabled || !chatId) return

    try {
      setIsLoading(true)
      setError(null)

      const response = await videoRAGApi.getSessionStatus(chatId, 'indexing')

      if (response.data.success) {
        const backendStatus = response.data

        // 检查状态是否发生变化
        const hasChanged = JSON.stringify(backendStatus) !== JSON.stringify(lastStatusRef.current)

        if (hasChanged) {
          lastStatusRef.current = backendStatus

          setBatchState(prevState => {
            const newState = mapBackendStatusToFrontend(backendStatus, prevState)

            // 检查是否有新完成的视频
            const newlyCompletedVideos = newState.videos.filter(video =>
              video.status === 'completed' &&
              prevState.videos.find(prev => prev.id === video.id)?.status !== 'completed'
            )

            // 触发视频完成回调
            newlyCompletedVideos.forEach(video => {
              onVideoCompleted?.(video)
            })

            // 检查批次是否完成
            if (backendStatus.status === 'completed' && prevState.status !== 'completed') {
              onBatchCompleted?.()
            }

            // 检查是否有错误
            if (backendStatus.status === 'error' && backendStatus.error) {
              onError?.(backendStatus.error)
            }

            return newState
          })
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '获取状态失败'
      setError(errorMessage)
      onError?.(errorMessage)
      console.error('Failed to fetch batch processing status:', err)
    } finally {
      setIsLoading(false)
    }
  }, [chatId, enabled, mapBackendStatusToFrontend, onVideoCompleted, onBatchCompleted, onError])

  // 开始轮询
  const startPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }

    // 立即执行一次
    fetchStatus()

    // 设置定时轮询
    intervalRef.current = setInterval(fetchStatus, pollingInterval)
  }, [fetchStatus, pollingInterval])

  // 停止轮询
  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  // 重试失败的视频
  const retryFailedVideos = useCallback(() => {
    const failedVideos = batchState.videos.filter(video => video.status === 'error')
    // 这里可以调用重试API
    console.log('Retrying failed videos:', failedVideos)
  }, [batchState.videos])

  // 暂停处理
  const pauseProcessing = useCallback(() => {
    setBatchState(prev => ({ ...prev, status: 'paused' }))
    stopPolling()
  }, [stopPolling])

  // 恢复处理
  const resumeProcessing = useCallback(() => {
    setBatchState(prev => ({ ...prev, status: 'processing' }))
    startPolling()
  }, [startPolling])

  // 重试单个视频
  const retryVideo = useCallback((videoId: string) => {
    const video = batchState.videos.find(v => v.id === videoId)
    if (video) {
      // 调用重试API
      console.log('Retrying video:', video)
      // 临时更新状态
      setBatchState(prev => ({
        ...prev,
        videos: prev.videos.map(v =>
          v.id === videoId
            ? { ...v, status: 'pending', error: undefined, retryCount: (v.retryCount || 0) + 1 }
            : v
        )
      }))
    }
  }, [batchState.videos])

  // 移除视频
  const removeVideo = useCallback((videoId: string) => {
    setBatchState(prev => {
      const updatedVideos = prev.videos.filter(v => v.id !== videoId)
      const newTotalVideos = prev.totalVideos - 1
      const newCompletedVideos = updatedVideos.filter(v => v.status === 'completed').length
      const newFailedVideos = updatedVideos.filter(v => v.status === 'error').length
      const newOverallProgress = newTotalVideos > 0 ? Math.round((newCompletedVideos / newTotalVideos) * 100) : 0

      return {
        ...prev,
        totalVideos: newTotalVideos,
        completedVideos: newCompletedVideos,
        failedVideos: newFailedVideos,
        overallProgress: newOverallProgress,
        videos: updatedVideos,
      }
    })
  }, [])

  // 更新视频列表
  const updateVideos = useCallback((videos: VideoProcessingItem[]) => {
    setBatchState(prev => ({
      ...prev,
      videos,
      totalVideos: videos.length,
      completedVideos: videos.filter(v => v.status === 'completed').length,
      failedVideos: videos.filter(v => v.status === 'error').length,
      overallProgress: videos.length > 0
        ? Math.round((videos.filter(v => v.status === 'completed').length / videos.length) * 100)
        : 0,
    }))
  }, [])

  // 初始化处理状态
  const initializeProcessing = useCallback((videos: VideoProcessingItem[]) => {
    const newBatchState: BatchProcessingState = {
      totalVideos: videos.length,
      completedVideos: 0,
      failedVideos: 0,
      overallProgress: 0,
      status: 'processing',
      videos,
      startTime: new Date(),
    }

    setBatchState(newBatchState)
    startPolling()
  }, [startPolling])

  // 自动启动轮询
  useEffect(() => {
    if (enabled && chatId) {
      startPolling()
    }

    return () => {
      stopPolling()
    }
  }, [enabled, chatId, startPolling, stopPolling])

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  return {
    batchState,
    isLoading,
    error,
    fetchStatus,
    startPolling,
    stopPolling,
    retryFailedVideos,
    pauseProcessing,
    resumeProcessing,
    retryVideo,
    removeVideo,
    updateVideos,
    initializeProcessing,
  }
}