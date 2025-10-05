import React, { useState, useEffect } from 'react'
import {
  BarChart3,
  Clock,
  CheckCircle,
  AlertTriangle,
  Pause,
  Play,
  RotateCcw,
  Minimize2,
  Maximize2,
  Filter,
  ChevronDown,
  ChevronUp,
  RefreshCw
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Progress } from './ui/progress'
import { Badge } from './ui/badge'
import VideoProcessingItemComponent from './VideoProcessingItem'
import MultiStageProgress from './MultiStageProgress'
import {
  BatchProcessingState,
  VideoProcessingItem as VideoProcessingItemType,
  ProcessingStats,
  formatProcessingTime,
  calculateSuccessRate
} from '../types/video'
import { cn } from '../lib/utils'

interface BatchProcessingProgressProps {
  batchState: BatchProcessingState
  onRetryVideo?: (videoId: string) => void
  onRemoveVideo?: (videoId: string) => void
  onPause?: () => void
  onResume?: () => void
  onRetryAll?: () => void
  className?: string
}

export default function BatchProcessingProgress({
  batchState,
  onRetryVideo,
  onRemoveVideo,
  onPause,
  onResume,
  onRetryAll,
  className
}: BatchProcessingProgressProps) {
  const [isMinimized, setIsMinimized] = useState(false)
  const [showCompletedOnly, setShowCompletedOnly] = useState(false)
  const [showErrorsOnly, setShowErrorsOnly] = useState(false)
  const [expandedVideos, setExpandedVideos] = useState<Set<string>>(new Set())

  // 计算处理统计
  const calculateStats = (): ProcessingStats => {
    const totalProcessed = batchState.completedVideos + batchState.failedVideos
    const successCount = batchState.completedVideos
    const errorCount = batchState.failedVideos
    const totalProcessingTime = batchState.endTime && batchState.startTime
      ? (batchState.endTime.getTime() - batchState.startTime.getTime()) / 1000
      : 0
    const averageTimePerVideo = successCount > 0 ? totalProcessingTime / successCount : 0
    const successRate = calculateSuccessRate(successCount, errorCount)

    return {
      totalProcessed,
      successCount,
      errorCount,
      averageTimePerVideo,
      totalProcessingTime,
      successRate
    }
  }

  const stats = calculateStats()

  // 过滤视频列表
  const getFilteredVideos = () => {
    let filtered = batchState.videos

    if (showCompletedOnly) {
      filtered = filtered.filter(v => v.status === 'completed')
    } else if (showErrorsOnly) {
      filtered = filtered.filter(v => v.status === 'error')
    }

    return filtered
  }

  const toggleVideoExpanded = (videoId: string) => {
    const newExpanded = new Set(expandedVideos)
    if (newExpanded.has(videoId)) {
      newExpanded.delete(videoId)
    } else {
      newExpanded.add(videoId)
    }
    setExpandedVideos(newExpanded)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processing':
        return 'bg-blue-500'
      case 'completed':
        return 'bg-green-500'
      case 'error':
        return 'bg-red-500'
      case 'paused':
        return 'bg-yellow-500'
      default:
        return 'bg-gray-500'
    }
  }

  const filteredVideos = getFilteredVideos()

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            批量处理进度
            <Badge variant="outline" className={cn("text-white", getStatusColor(batchState.status))}>
              {batchState.status === 'processing' && '处理中'}
              {batchState.status === 'completed' && '已完成'}
              {batchState.status === 'error' && '出现错误'}
              {batchState.status === 'paused' && '已暂停'}
              {batchState.status === 'uploading' && '上传中'}
            </Badge>
          </CardTitle>

          <div className="flex items-center gap-2">
            {/* 控制按钮 */}
            {batchState.status === 'processing' && onPause && (
              <Button variant="outline" size="sm" onClick={onPause}>
                <Pause className="w-4 h-4 mr-1" />
                暂停
              </Button>
            )}

            {batchState.status === 'paused' && onResume && (
              <Button variant="outline" size="sm" onClick={onResume}>
                <Play className="w-4 h-4 mr-1" />
                继续
              </Button>
            )}

            {(batchState.status === 'error' || batchState.failedVideos > 0) && onRetryAll && (
              <Button variant="outline" size="sm" onClick={onRetryAll}>
                <RefreshCw className="w-4 h-4 mr-1" />
                重试失败项
              </Button>
            )}

            {/* 最小化按钮 */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMinimized(!isMinimized)}
            >
              {isMinimized ? (
                <Maximize2 className="w-4 h-4" />
              ) : (
                <Minimize2 className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>

      {!isMinimized && (
        <CardContent className="space-y-6">
          {/* 总体进度概览 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {batchState.totalVideos}
              </div>
              <div className="text-sm text-blue-700">总视频数</div>
            </div>

            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {batchState.completedVideos}
              </div>
              <div className="text-sm text-green-700">已完成</div>
            </div>

            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {batchState.failedVideos}
              </div>
              <div className="text-sm text-red-700">失败</div>
            </div>

            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {stats.successRate}%
              </div>
              <div className="text-sm text-purple-700">成功率</div>
            </div>
          </div>

          {/* 整体进度条 */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">整体进度</span>
              <span className="text-sm text-muted-foreground">
                {batchState.completedVideos + batchState.failedVideos} / {batchState.totalVideos}
              </span>
            </div>
            <Progress value={batchState.overallProgress} className="h-3" />
          </div>

          {/* 时间信息 */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                <span>总用时: {formatProcessingTime(stats.totalProcessingTime)}</span>
              </div>
              {stats.averageTimePerVideo > 0 && (
                <div>平均: {formatProcessingTime(stats.averageTimePerVideo)}/视频</div>
              )}
              {batchState.estimatedTimeRemaining && batchState.status === 'processing' && (
                <div className="text-blue-600">
                  预计剩余: {formatProcessingTime(batchState.estimatedTimeRemaining)}
                </div>
              )}
            </div>

            {batchState.currentProcessingVideo && (
              <div className="text-blue-600 font-medium">
                正在处理: {batchState.currentProcessingVideo}
              </div>
            )}
          </div>

          {/* 当前处理阶段 */}
          {batchState.videos.some(v => v.status === 'processing') && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium mb-3">当前处理阶段</h4>
              {batchState.videos
                .filter(v => v.status === 'processing')
                .map(video => (
                  <div key={video.id} className="mb-3 last:mb-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">{video.name}</span>
                      <span className="text-xs text-muted-foreground">{video.progress}%</span>
                    </div>
                    <Progress value={video.progress} className="h-1" />
                  </div>
                ))}
            </div>
          )}

          {/* 过滤器 */}
          <div className="flex items-center gap-2">
            <Button
              variant={showCompletedOnly ? "default" : "outline"}
              size="sm"
              onClick={() => {
                setShowCompletedOnly(!showCompletedOnly)
                setShowErrorsOnly(false)
              }}
            >
              <CheckCircle className="w-4 h-4 mr-1" />
              仅显示完成 ({batchState.completedVideos})
            </Button>

            <Button
              variant={showErrorsOnly ? "default" : "outline"}
              size="sm"
              onClick={() => {
                setShowErrorsOnly(!showErrorsOnly)
                setShowCompletedOnly(false)
              }}
            >
              <AlertTriangle className="w-4 h-4 mr-1" />
              仅显示错误 ({batchState.failedVideos})
            </Button>

            {(showCompletedOnly || showErrorsOnly) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setShowCompletedOnly(false)
                  setShowErrorsOnly(false)
                }}
              >
                显示全部
              </Button>
            )}
          </div>

          {/* 视频列表 */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-medium">
                视频列表 {showCompletedOnly || showErrorsOnly ? `(已过滤)` : ''}
              </h4>
              <div className="text-sm text-muted-foreground">
                显示 {filteredVideos.length} / {batchState.videos.length} 个视频
              </div>
            </div>

            <div className="space-y-3 max-h-96 overflow-y-auto">
              {filteredVideos.map(video => (
                <VideoProcessingItemComponent
                  key={video.id}
                  video={video}
                  isExpanded={expandedVideos.has(video.id)}
                  onToggleExpand={() => toggleVideoExpanded(video.id)}
                  onRetry={onRetryVideo}
                  onRemove={onRemoveVideo}
                />
              ))}

              {filteredVideos.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  {showCompletedOnly && "没有已完成的视频"}
                  {showErrorsOnly && "没有失败的视频"}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  )
}